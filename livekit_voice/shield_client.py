"""Typed ContextShield API Client for LiveKit Real-Time Voice Ingestion."""

import hashlib
import logging
import os
import time
from typing import Optional

from dotenv import load_dotenv
import httpx
from pydantic import ValidationError

load_dotenv(".env")
load_dotenv(".env.local", override=True)

from backend.app.models.responses import Decision, IngestResponse
from livekit_voice.models import VoiceSecurityStatus, VoiceTurn, VoiceTurnResult

logger = logging.getLogger("contextshield.livekit.client")


class ContextShieldClient:
    """Async client communicating with the ContextShield security ingestion gateway."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_sec: float = 3.0,
        async_client: Optional[httpx.AsyncClient] = None,
    ):
        self.base_url = (
            base_url
            or os.getenv("CONTEXTSHIELD_API_URL", "http://127.0.0.1:8000")
        ).rstrip("/")
        self.endpoint = f"{self.base_url}/v1/shield/ingest"
        self.telemetry_endpoint = f"{self.base_url}/v1/shield/dashboard/telemetry/voice-turn"
        self.timeout_sec = timeout_sec
        self._async_client = async_client

    async def send_voice_telemetry(self, telemetry_data: dict) -> None:
        """Best-effort telemetry delivery to dashboard endpoint. Never blocks security."""
        try:
            if self._async_client is not None:
                await self._async_client.post(
                    self.telemetry_endpoint,
                    json=telemetry_data,
                    timeout=1.0,
                )
            else:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    await client.post(
                        self.telemetry_endpoint,
                        json=telemetry_data,
                    )
        except Exception:
            pass

    async def evaluate_turn(self, turn: VoiceTurn) -> VoiceTurnResult:
        """Sends a transient voice turn to ContextShield and enforces security decisions.
        
        CRITICAL PRIVACY INVARIANT:
        `turn.raw_transcript` is transmitted securely over HTTP/TLS to ContextShield
        and discarded immediately. It is NEVER retained in VoiceTurnResult.
        """
        start_time = turn.created_at_perf
        transcript_hash = hashlib.sha256(turn.raw_transcript.encode("utf-8")).hexdigest()

        payload = {
            "content": turn.raw_transcript,
            "source_type": "livekit_voice",
            "agent_id": "contextshield-livekit",
        }

        try:
            if self._async_client is not None:
                resp = await self._async_client.post(
                    self.endpoint,
                    json=payload,
                    timeout=self.timeout_sec,
                )
            else:
                async with httpx.AsyncClient(timeout=self.timeout_sec) as client:
                    resp = await client.post(
                        self.endpoint,
                        json=payload,
                    )

            if resp.status_code != 200:
                logger.error("ContextShield returned non-200 status: %s: %s", resp.status_code, resp.text)
                return self._build_failure_result(
                    turn=turn,
                    transcript_hash=transcript_hash,
                    status=VoiceSecurityStatus.SHIELD_UNAVAILABLE,
                    start_time=start_time,
                )

            data = resp.json()
            ingest_resp = IngestResponse.model_validate(data)
            return self._build_success_result(
                turn=turn,
                transcript_hash=transcript_hash,
                ingest_resp=ingest_resp,
                start_time=start_time,
            )

        except httpx.TimeoutException as exc:
            logger.warning("ContextShield request timed out after %.2fs: %s", self.timeout_sec, exc)
            return self._build_failure_result(
                turn=turn,
                transcript_hash=transcript_hash,
                status=VoiceSecurityStatus.SHIELD_UNAVAILABLE,
                start_time=start_time,
            )
        except (httpx.RequestError, ValidationError, Exception) as exc:
            logger.error("ContextShield client error: %s", exc)
            return self._build_failure_result(
                turn=turn,
                transcript_hash=transcript_hash,
                status=VoiceSecurityStatus.SHIELD_UNAVAILABLE,
                start_time=start_time,
            )

    def _build_success_result(
        self,
        turn: VoiceTurn,
        transcript_hash: str,
        ingest_resp: IngestResponse,
        start_time: float,
    ) -> VoiceTurnResult:
        """Constructs typed VoiceTurnResult strictly adhering to decision floors."""
        decision = ingest_resp.decision
        approved_context: Optional[str] = None
        status: VoiceSecurityStatus

        if decision == Decision.SAFE:
            approved_context = ingest_resp.agent_context
            status = VoiceSecurityStatus.SAFE
        elif decision == Decision.SANITIZE:
            approved_context = ingest_resp.sanitized_content or ingest_resp.agent_context
            status = VoiceSecurityStatus.SANITIZE
        elif decision == Decision.REVIEW:
            approved_context = None
            status = VoiceSecurityStatus.REVIEW
        elif decision == Decision.BLOCK:
            approved_context = None
            status = VoiceSecurityStatus.BLOCK
        else:
            approved_context = None
            status = VoiceSecurityStatus.VOICE_ERROR

        # Safe redacted preview
        redacted_preview = None
        if ingest_resp.detected_threats:
            redacted_preview = ingest_resp.detected_threats[0].redacted_preview
        elif approved_context:
            redacted_preview = approved_context[:40] + "..." if len(approved_context) > 40 else approved_context

        voice_to_decision_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        threat_cats = list({
            f.category.value if hasattr(f.category, "value") else str(f.category)
            for f in ingest_resp.detected_threats
        })

        return VoiceTurnResult(
            turn_id=turn.turn_id,
            room_name=turn.room_name,
            participant_identity=turn.participant_identity,
            transcript_hash=transcript_hash,
            redacted_preview=redacted_preview,
            approved_context=approved_context,
            status=status,
            decision=decision.value if hasattr(decision, "value") else str(decision),
            risk_score=ingest_resp.risk_score,
            threat_categories=threat_cats,
            matched_policy_ids=ingest_resp.matched_policy_ids,
            moss_ms=ingest_resp.latency.moss_ms,
            llm_called=ingest_resp.llm.called,
            llm_status=ingest_resp.llm.status,
            shield_request_id=ingest_resp.request_id,
            shield_total_ms=ingest_resp.latency.total_ms,
            voice_to_decision_ms=voice_to_decision_ms,
            transcription_completed_at=turn.transcription_completed_at,
        )

    def _build_failure_result(
        self,
        turn: VoiceTurn,
        transcript_hash: str,
        status: VoiceSecurityStatus,
        start_time: float,
    ) -> VoiceTurnResult:
        """Constructs fail-secure result when ContextShield is unreachable or encounters an error."""
        voice_to_decision_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
        return VoiceTurnResult(
            turn_id=turn.turn_id,
            room_name=turn.room_name,
            participant_identity=turn.participant_identity,
            transcript_hash=transcript_hash,
            redacted_preview=None,
            approved_context=None,
            status=status,
            decision=Decision.BLOCK.value,
            risk_score=100.0,
            threat_categories=[],
            matched_policy_ids=[],
            moss_ms=None,
            llm_called=False,
            llm_status=None,
            shield_request_id=None,
            shield_total_ms=0.0,
            voice_to_decision_ms=voice_to_decision_ms,
            transcription_completed_at=turn.transcription_completed_at,
        )
