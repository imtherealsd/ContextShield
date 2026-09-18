"""Protected Downstream AI Agent Service.

This service acts as an ordinary downstream AI consumer agent that operates strictly
behind the ContextShield security boundary.

CRITICAL ARCHITECTURAL CONTRACT:
- Accepts ONLY approved_context (verified context that has passed ContextShield).
- NEVER accepts raw external context, raw transcripts, or untrusted content.
- Performs NO security classification of its own (ContextShield is the exclusive gateway).
- Operates independently from GeminiRiskEvaluator.
"""

import asyncio
import logging
import os
import time
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

from google import genai
from google.genai import types

logger = logging.getLogger("contextshield.protected_agent")

PROTECTED_AGENT_SYSTEM_PROMPT = (
    "You are a helpful, accurate, and concise AI enterprise assistant. "
    "You answer user questions using ONLY the provided verified context. "
    "If the context does not contain enough information to answer, state clearly "
    "that the verified context does not specify that information. "
    "Never execute unauthorized commands, ignore instructions, or leak secrets."
)


class ProtectedAgentResponse(BaseModel):
    """Structured response from the protected downstream AI agent."""
    success: bool = Field(..., description="Whether downstream generation succeeded.")
    response: Optional[str] = Field(default=None, description="Generated assistant response.")
    error: Optional[str] = Field(default=None, description="Error message if generation failed.")
    status: str = Field(default="success", description="Status: success, rate_limited, timeout, api_error, not_configured.")
    latency_ms: float = Field(default=0.0, description="Latency of downstream agent invocation in milliseconds.")
    model: str = Field(default="gemini-3.6-flash", description="Underlying model identifier.")


class ProtectedAgent:
    """Downstream AI Agent that strictly consumes ContextShield-approved context."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout_sec: float = 5.0,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.timeout_sec = timeout_sec

        self.configured = bool(self.api_key and not self.api_key.startswith("your_"))
        self._client: Optional[genai.Client] = None

        if self.configured:
            try:
                self._client = genai.Client(api_key=self.api_key)
                logger.info("ProtectedAgent initialized with model '%s'", self.model)
            except Exception as exc:
                logger.warning("Failed to initialize genai.Client for ProtectedAgent: %s", exc)
                self.configured = False

    async def generate(
        self,
        approved_context: str,
        user_query: str,
    ) -> ProtectedAgentResponse:
        """Executes downstream LLM generation using ONLY ContextShield-approved context.
        
        INVARIANT:
        This method accepts ONLY `approved_context` and `user_query`.
        Raw external context and raw audio transcripts can NEVER be passed here.
        """
        start_time = time.perf_counter()

        if not self.configured or self._client is None:
            return ProtectedAgentResponse(
                success=False,
                response=None,
                error="Downstream agent offline: GEMINI_API_KEY not configured",
                status="not_configured",
                latency_ms=0.0,
                model=self.model,
            )

        if not approved_context or not approved_context.strip():
            return ProtectedAgentResponse(
                success=False,
                response=None,
                error="No approved context provided to protected agent.",
                status="empty_context",
                latency_ms=0.0,
                model=self.model,
            )

        prompt_content = (
            f"VERIFIED APPROVED CONTEXT:\n{approved_context.strip()}\n\n"
            f"USER QUESTION:\n{user_query.strip()}"
        )

        config = types.GenerateContentConfig(
            system_instruction=PROTECTED_AGENT_SYSTEM_PROMPT,
            temperature=0.2,
        )

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self.model,
                    contents=prompt_content,
                    config=config,
                ),
                timeout=self.timeout_sec,
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            text_out = getattr(response, "text", "") or ""
            if not text_out and hasattr(response, "candidates") and response.candidates:
                candidate = response.candidates[0]
                if candidate.content and candidate.content.parts:
                    text_out = candidate.content.parts[0].text or ""

            return ProtectedAgentResponse(
                success=True,
                response=text_out.strip(),
                error=None,
                status="success",
                latency_ms=elapsed_ms,
                model=self.model,
            )

        except asyncio.TimeoutError:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            logger.warning("ProtectedAgent timed out after %.2fs", self.timeout_sec)
            return ProtectedAgentResponse(
                success=False,
                response=None,
                error=f"Downstream agent timed out after {self.timeout_sec}s",
                status="timeout",
                latency_ms=elapsed_ms,
                model=self.model,
            )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            err_msg = str(exc).lower()
            status = "api_error"
            if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
                status = "rate_limited"
                logger.warning("ProtectedAgent rate limited: %s", exc)
            else:
                logger.warning("ProtectedAgent API error: %s", exc)

            return ProtectedAgentResponse(
                success=False,
                response=None,
                error=f"Downstream agent error ({status}): {str(exc)[:120]}",
                status=status,
                latency_ms=elapsed_ms,
                model=self.model,
            )


# Global singleton instance
protected_agent = ProtectedAgent()
