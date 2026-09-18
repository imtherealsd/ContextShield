"""Contextual LLM Security Risk Evaluator for ContextShield.

Uses Google Gemini as its exclusive LLM evaluator via the official google-genai SDK.
Maintains a clean provider abstraction:
    BaseRiskEvaluator
           |
    GeminiRiskEvaluator

Enforces:
- Hard latency deadline (LLM_HARD_TIMEOUT_MS) via asyncio.wait_for()
- Target latency tracking (LLM_TARGET_LATENCY_MS) with target_exceeded telemetry
- Rate limit / quota handling (status: rate_limited, fail secure)
- Structured JSON schema enforcement with Pydantic model
- Policy hallucination filtering against real Moss retrieval
- Threat category validation
"""

from abc import ABC, abstractmethod
import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv
from pydantic import ValidationError

load_dotenv()

from google import genai
from google.genai import types

from backend.app.models.requests import SourceType
from backend.app.models.responses import (
    Decision,
    LLMIngestStatus,
    LLMRiskEvaluation,
    MossPolicyMatch,
    Severity,
    ThreatCategory,
    ThreatFinding,
)
from backend.app.prompts.risk_evaluator import (
    PROMPT_HASH,
    PROMPT_VERSION,
    RISK_EVALUATOR_SYSTEM_PROMPT,
)

logger = logging.getLogger("contextshield.evaluator")


class BaseRiskEvaluator(ABC):
    """Abstract base class for contextual LLM risk evaluators."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        target_latency_ms: Optional[float] = None,
        hard_timeout_ms: Optional[float] = None,
    ):
        self.prompt_version = PROMPT_VERSION
        self.prompt_hash = PROMPT_HASH

        self.target_latency_ms = (
            target_latency_ms
            if target_latency_ms is not None
            else float(os.getenv("LLM_TARGET_LATENCY_MS", os.getenv("LLM_PRIMARY_TIMEOUT_MS", "800")))
        )
        self.hard_timeout_ms = (
            hard_timeout_ms
            if hard_timeout_ms is not None
            else float(os.getenv("LLM_HARD_TIMEOUT_MS", "1500"))
        )
        self.timeout_sec = self.hard_timeout_ms / 1000.0

    @property
    @abstractmethod
    def provider(self) -> str:
        """Provider identifier string (e.g. 'gemini')."""
        pass

    @property
    @abstractmethod
    def configured(self) -> bool:
        """Whether this provider has valid credentials and client ready."""
        pass

    @property
    @abstractmethod
    def model(self) -> Optional[str]:
        """Configured model identifier."""
        pass

    def _build_payload(
        self,
        source_type: Union[SourceType, str],
        untrusted_content: str,
        deterministic_findings: List[ThreatFinding],
        moss_findings: Union[List[MossPolicyMatch], List[Dict[str, Any]]],
    ) -> str:
        """Builds strict structured user payload — untrusted context is pure DATA."""
        findings_payload = [
            {
                "rule_id": f.rule_id,
                "category": f.category.value if hasattr(f.category, "value") else str(f.category),
                "severity": f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            }
            for f in deterministic_findings
        ]

        moss_payload = []
        for m in moss_findings:
            if isinstance(m, MossPolicyMatch):
                moss_payload.append({
                    "id": m.id,
                    "score": m.score,
                    "category": m.category,
                    "severity": m.severity,
                    "recommended_action": m.recommended_action,
                })
            elif isinstance(m, dict):
                moss_payload.append({
                    "id": m.get("id"),
                    "score": m.get("score"),
                    "category": m.get("category"),
                    "severity": m.get("severity"),
                    "recommended_action": m.get("recommended_action"),
                })

        user_payload_dict = {
            "source_type": source_type.value if hasattr(source_type, "value") else str(source_type),
            "untrusted_content": untrusted_content,
            "deterministic_findings": findings_payload,
            "moss_findings": moss_payload,
        }
        return json.dumps(user_payload_dict, ensure_ascii=False)

    def _sanitize_evaluation(
        self,
        parsed_eval: Optional[LLMRiskEvaluation],
        moss_findings: Union[List[MossPolicyMatch], List[Dict[str, Any]]],
    ) -> Tuple[Optional[LLMRiskEvaluation], int]:
        """Enforces security invariants on LLM evaluation outputs:
        1. Discards hallucinated Moss policy IDs not present in actual Moss retrieval.
        2. Filters out unrecognized threat categories against ThreatCategory enum.
        """
        if parsed_eval is None:
            return None, 0

        allowed_policy_ids = set()
        for m in moss_findings:
            if isinstance(m, MossPolicyMatch):
                allowed_policy_ids.add(m.id)
            elif isinstance(m, dict) and m.get("id"):
                allowed_policy_ids.add(str(m.get("id")))
            elif isinstance(m, str):
                allowed_policy_ids.add(m)

        llm_pids = list(parsed_eval.matched_policy_ids or [])
        valid_pids = [pid for pid in llm_pids if pid in allowed_policy_ids]
        invalid_policy_count = len(llm_pids) - len(valid_pids)

        supported_categories = {cat.value for cat in ThreatCategory}
        valid_cats = []
        for cat in (parsed_eval.threat_categories or []):
            cat_str = cat.value if isinstance(cat, ThreatCategory) else str(cat)
            if cat_str in supported_categories:
                valid_cats.append(cat_str)

        sanitized_eval = parsed_eval.model_copy(update={
            "matched_policy_ids": valid_pids,
            "threat_categories": valid_cats,
        })
        return sanitized_eval, invalid_policy_count

    @abstractmethod
    async def evaluate(
        self,
        source_type: Union[SourceType, str],
        untrusted_content: str,
        deterministic_findings: List[ThreatFinding],
        moss_findings: Union[List[MossPolicyMatch], List[Dict[str, Any]]],
        reason_called: str = "ambiguous_context",
    ) -> Tuple[Optional[LLMRiskEvaluation], LLMIngestStatus, float]:
        """Evaluates ambiguous context returning (evaluation, status, elapsed_ms)."""
        pass


class GeminiRiskEvaluator(BaseRiskEvaluator):
    """Contextual LLM Risk Evaluator using Google GenAI SDK structured outputs."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        target_latency_ms: Optional[float] = None,
        hard_timeout_ms: Optional[float] = None,
    ):
        super().__init__(
            api_key=api_key,
            model=model,
            target_latency_ms=target_latency_ms,
            hard_timeout_ms=hard_timeout_ms,
        )
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

        self._client: Optional[genai.Client] = None
        if self.api_key:
            http_options = types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1),
            )
            self._client = genai.Client(api_key=self.api_key, http_options=http_options)
        self._configured_override: Optional[bool] = None

    @property
    def provider(self) -> str:
        return "gemini"

    @property
    def model(self) -> Optional[str]:
        return self._model

    @model.setter
    def model(self, val: Optional[str]) -> None:
        self._model = val

    @property
    def client(self) -> Optional[genai.Client]:
        return self._client

    @client.setter
    def client(self, c: Optional[genai.Client]) -> None:
        self._client = c

    @property
    def configured(self) -> bool:
        if self._configured_override is not None:
            return self._configured_override
        if not self.api_key:
            load_dotenv()
            self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key and not self._client:
            http_options = types.HttpOptions(
                retry_options=types.HttpRetryOptions(attempts=1),
            )
            self._client = genai.Client(api_key=self.api_key, http_options=http_options)
        return bool(self._client and self.api_key)

    @configured.setter
    def configured(self, val: bool) -> None:
        self._configured_override = val

    async def evaluate(
        self,
        source_type: Union[SourceType, str],
        untrusted_content: str,
        deterministic_findings: List[ThreatFinding],
        moss_findings: Union[List[MossPolicyMatch], List[Dict[str, Any]]],
        reason_called: str = "ambiguous_context",
    ) -> Tuple[Optional[LLMRiskEvaluation], LLMIngestStatus, float]:
        """Evaluates ambiguous context using Google GenAI structured outputs.
        
        Security Controls:
        - Structured JSON schema enforcement with Pydantic model.
        - Independent validation of model output via LLMRiskEvaluation.model_validate_json.
        - Hard latency deadline enforced via asyncio.wait_for() (LLM_HARD_TIMEOUT_MS).
        - Target latency tracking (LLM_TARGET_LATENCY_MS) with target_exceeded telemetry.
        - Explicit quota / rate limit handling (status: rate_limited, fail secure).
        - External data is strictly dynamic payload; system prompt is static.
        - Strictly classification-only (no search, URL context, code exec, function tools).
        - Discards hallucinated policy IDs and unsupported threat categories.
        """
        if not self.configured:
            status_obj = LLMIngestStatus(
                provider=self.provider,
                status="not_configured",
                model=self.model,
                prompt_version=self.prompt_version,
                prompt_hash=self.prompt_hash,
                called=False,
                reason_called=reason_called,
                target_latency_ms=self.target_latency_ms,
                hard_timeout_ms=self.hard_timeout_ms,
                target_exceeded=None,
                provider_request_id=None,
            )
            return None, status_obj, 0.0

        start_time = time.perf_counter()
        user_payload_json = self._build_payload(
            source_type, untrusted_content, deterministic_findings, moss_findings
        )

        parsed_eval: Optional[LLMRiskEvaluation] = None
        status = "api_error"
        provider_request_id: Optional[str] = None

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LLMRiskEvaluation,
            system_instruction=RISK_EVALUATOR_SYSTEM_PROMPT,
            temperature=0.0,
        )

        try:
            # Enforce hard latency budget using asyncio.wait_for
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self.model,
                    contents=user_payload_json,
                    config=config,
                ),
                timeout=self.timeout_sec,
            )

            # Extract raw response text and independently validate against Pydantic schema
            raw_text = getattr(response, "text", "") or ""
            if not raw_text and hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    raw_text = candidate.content.parts[0].text or ""

            if not raw_text:
                status = "schema_error"
            else:
                try:
                    parsed_eval = LLMRiskEvaluation.model_validate_json(raw_text)
                    status = "success"
                except (ValidationError, ValueError) as val_err:
                    logger.warning("Pydantic validation of Gemini response failed: %s", val_err)
                    status = "schema_error"

        except asyncio.TimeoutError:
            logger.warning("Gemini evaluator timed out after %.3fs hard deadline", self.timeout_sec)
            status = "timeout"
        except ValidationError as e:
            logger.warning("Gemini evaluator schema validation error: %s", e)
            status = "schema_error"
        except Exception as e:
            err_msg = str(e).lower()
            if (
                "429" in err_msg
                or "resource_exhausted" in err_msg
                or "quota" in err_msg
                or "rate_limit" in err_msg
                or "rate limit" in err_msg
            ):
                logger.warning("Gemini rate limit / quota exceeded: %s", e)
                status = "rate_limited"
            elif (
                "404" in err_msg
                or "not found" in err_msg
                or "no longer available" in err_msg
                or "does not exist" in err_msg
            ):
                logger.warning("Configured Gemini model '%s' is unavailable: %s", self.model, e)
                status = "model_unavailable"
            elif "timeout" in err_msg or "timed out" in err_msg:
                status = "timeout"
            elif "json" in err_msg or "schema" in err_msg:
                status = "schema_error"
            else:
                logger.error("Gemini API error during risk evaluation: %s", e)
                status = "api_error"

        parsed_eval, invalid_policy_count = self._sanitize_evaluation(parsed_eval, moss_findings)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        # Target latency tracking
        target_exceeded: Optional[bool] = None
        if status == "success":
            target_exceeded = elapsed_ms > self.target_latency_ms
        elif status == "timeout":
            target_exceeded = True

        status_obj = LLMIngestStatus(
            provider=self.provider,
            status=status,
            model=self.model,
            prompt_version=self.prompt_version,
            prompt_hash=self.prompt_hash,
            called=True,
            reason_called=reason_called,
            target_latency_ms=self.target_latency_ms,
            hard_timeout_ms=self.hard_timeout_ms,
            target_exceeded=target_exceeded,
            provider_request_id=provider_request_id,
            invalid_llm_policy_ids_count=invalid_policy_count,
        )
        return parsed_eval, status_obj, elapsed_ms


class ContextualEvaluatorRouter(BaseRiskEvaluator):
    """Provider router directing evaluations to active provider (Gemini)."""

    def __init__(self):
        super().__init__()
        self.gemini_evaluator = GeminiRiskEvaluator()

    @property
    def provider(self) -> str:
        load_dotenv()
        return os.getenv("LLM_PROVIDER", "gemini").lower()

    @property
    def active_evaluator(self) -> Optional[BaseRiskEvaluator]:
        prov = self.provider
        if prov == "gemini":
            return self.gemini_evaluator
        return None

    @property
    def configured(self) -> bool:
        evaluator = self.active_evaluator
        if evaluator is None:
            return False
        return evaluator.configured

    @configured.setter
    def configured(self, val: bool) -> None:
        evaluator = self.active_evaluator
        if evaluator is not None and hasattr(evaluator, "configured"):
            evaluator.configured = val

    @property
    def model(self) -> Optional[str]:
        evaluator = self.active_evaluator
        return evaluator.model if evaluator else None

    @model.setter
    def model(self, val: Optional[str]) -> None:
        evaluator = self.active_evaluator
        if evaluator and hasattr(evaluator, "model"):
            evaluator.model = val

    @property
    def client(self) -> Any:
        evaluator = self.active_evaluator
        return getattr(evaluator, "client", None) if evaluator else None

    @client.setter
    def client(self, c: Any) -> None:
        evaluator = self.active_evaluator
        if evaluator and hasattr(evaluator, "client"):
            evaluator.client = c

    @property
    def _client(self) -> Any:
        evaluator = self.active_evaluator
        return getattr(evaluator, "_client", None) or getattr(evaluator, "client", None)

    @_client.setter
    def _client(self, c: Any) -> None:
        evaluator = self.active_evaluator
        if evaluator:
            if hasattr(evaluator, "_client"):
                evaluator._client = c
            if hasattr(evaluator, "client"):
                evaluator.client = c

    @property
    def api_key(self) -> Optional[str]:
        evaluator = self.active_evaluator
        return getattr(evaluator, "api_key", None) if evaluator else None

    @api_key.setter
    def api_key(self, val: Optional[str]) -> None:
        evaluator = self.active_evaluator
        if evaluator and hasattr(evaluator, "api_key"):
            evaluator.api_key = val

    async def evaluate(
        self,
        source_type: Union[SourceType, str],
        untrusted_content: str,
        deterministic_findings: List[ThreatFinding],
        moss_findings: Union[List[MossPolicyMatch], List[Dict[str, Any]]],
        reason_called: str = "ambiguous_context",
    ) -> Tuple[Optional[LLMRiskEvaluation], LLMIngestStatus, float]:
        evaluator = self.active_evaluator
        if evaluator is None:
            # Invalid provider fails secure with explicit invalid_provider status
            invalid_prov = self.provider
            logger.warning("Invalid LLM provider configured: '%s'. Failing secure.", invalid_prov)
            status_obj = LLMIngestStatus(
                provider=invalid_prov,
                status="invalid_provider",
                model=None,
                prompt_version=self.prompt_version,
                prompt_hash=self.prompt_hash,
                called=False,
                reason_called=reason_called,
                target_latency_ms=self.target_latency_ms,
                hard_timeout_ms=self.hard_timeout_ms,
                target_exceeded=None,
                provider_request_id=None,
            )
            return None, status_obj, 0.0

        return await evaluator.evaluate(
            source_type=source_type,
            untrusted_content=untrusted_content,
            deterministic_findings=deterministic_findings,
            moss_findings=moss_findings,
            reason_called=reason_called,
        )


# Backward compatibility alias
ContextualLLMEvaluator = GeminiRiskEvaluator

# Global evaluator service singleton
evaluator_service = ContextualEvaluatorRouter()
