"""Security and Telemetry Data Models for LiveKit Real-Time Voice Ingestion."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class VoiceSecurityStatus(str, Enum):
    """Voice ingestion security and operational status."""
    SAFE = "SAFE"
    SANITIZE = "SANITIZE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"
    VOICE_ERROR = "VOICE_ERROR"
    SHIELD_UNAVAILABLE = "SHIELD_UNAVAILABLE"
    TRANSCRIPTION_ERROR = "TRANSCRIPTION_ERROR"


class VoiceTurn:
    """Transient in-memory container for an unverified audio turn awaiting evaluation.
    
    CRITICAL PRIVACY INVARIANT:
    `raw_transcript` exists only transiently in memory during evaluation and must
    NEVER be serialized to VoiceTurnResult, RoomSecurityEvent, logs, or downstream agents.
    """
    __slots__ = (
        "turn_id",
        "room_name",
        "participant_identity",
        "raw_transcript",
        "transcription_completed_at",
        "created_at_perf",
    )

    def __init__(
        self,
        turn_id: str,
        room_name: str,
        participant_identity: str,
        raw_transcript: str,
        transcription_completed_at: str,
        created_at_perf: float,
    ):
        self.turn_id = turn_id
        self.room_name = room_name
        self.participant_identity = participant_identity
        self.raw_transcript = raw_transcript
        self.transcription_completed_at = transcription_completed_at
        self.created_at_perf = created_at_perf


class VoiceTurnResult(BaseModel):
    """Final validated security result for a voice turn.
    
    Contains strictly approved context, safe hashes, and telemetry.
    Zero raw hostile voice transcript serialized.
    """
    model_config = ConfigDict(extra="forbid")

    turn_id: str = Field(..., description="Unique turn identifier.")
    room_name: str = Field(..., description="LiveKit room name.")
    participant_identity: str = Field(..., description="Speaker identity.")
    transcript_hash: str = Field(..., description="SHA-256 hash of the voice transcript.")
    redacted_preview: Optional[str] = Field(default=None, description="Safe redacted preview of input.")
    approved_context: Optional[str] = Field(
        default=None,
        description="Approved context forwarded to downstream agent. None for REVIEW, BLOCK, or ERROR."
    )
    status: VoiceSecurityStatus = Field(..., description="Voice operational or security status.")
    decision: Optional[str] = Field(default=None, description="ContextShield decision: SAFE, SANITIZE, REVIEW, BLOCK.")
    risk_score: float = Field(default=0.0, description="Evaluated risk score (0.0 - 100.0).")
    threat_categories: List[str] = Field(default_factory=list, description="Detected threat categories.")
    matched_policy_ids: List[str] = Field(default_factory=list, description="Matched security policy IDs.")
    moss_ms: Optional[float] = Field(default=None, description="Moss retrieval latency in ms.")
    llm_called: bool = Field(default=False, description="Whether contextual LLM was invoked.")
    llm_status: Optional[str] = Field(default=None, description="LLM execution status.")
    shield_request_id: Optional[str] = Field(default=None, description="ContextShield API request ID.")
    shield_total_ms: float = Field(default=0.0, description="ContextShield total latency in ms.")
    voice_to_decision_ms: float = Field(..., description="Total end-to-end latency from STT finish to decision.")
    transcription_completed_at: str = Field(..., description="Timestamp when STT finished.")


class RoomSecurityEvent(BaseModel):
    """Safe realtime event published to the LiveKit room via local_participant.publish_data.
    
    Used by the real-time security dashboard.
    CRITICAL: Contains zero raw transcripts, zero credentials, zero API secrets.
    """
    model_config = ConfigDict(extra="forbid")

    event: str = Field(default="contextshield.security_result", description="Event name.")
    turn_id: str = Field(..., description="Unique turn identifier.")
    request_id: Optional[str] = Field(default=None, description="ContextShield request ID.")
    source: str = Field(default="livekit_voice", description="Ingestion source channel.")
    decision: str = Field(..., description="Security decision: SAFE, SANITIZE, REVIEW, BLOCK, ERROR.")
    risk_score: float = Field(default=0.0, description="Risk score.")
    threat_categories: List[str] = Field(default_factory=list, description="Detected threat categories.")
    matched_policy_ids: List[str] = Field(default_factory=list, description="Matched policy IDs.")
    moss_ms: Optional[float] = Field(default=None, description="Moss retrieval latency in ms.")
    llm_called: bool = Field(default=False, description="Whether LLM was called.")
    llm_status: Optional[str] = Field(default=None, description="LLM status.")
    shield_total_ms: float = Field(default=0.0, description="ContextShield latency in ms.")
    voice_to_decision_ms: float = Field(..., description="End-to-end latency in ms.")
    redacted_preview: Optional[str] = Field(default=None, description="Safe redacted preview.")

    @classmethod
    def from_voice_turn_result(cls, result: "VoiceTurnResult") -> "RoomSecurityEvent":
        """Factory method to convert a VoiceTurnResult into a safe RoomSecurityEvent."""
        return cls(
            event="contextshield.security_result",
            turn_id=result.turn_id,
            request_id=result.shield_request_id,
            source="livekit_voice",
            decision=result.decision or "BLOCK",
            risk_score=result.risk_score,
            threat_categories=result.threat_categories,
            matched_policy_ids=result.matched_policy_ids,
            moss_ms=result.moss_ms,
            llm_called=result.llm_called,
            llm_status=result.llm_status,
            shield_total_ms=result.shield_total_ms,
            voice_to_decision_ms=result.voice_to_decision_ms,
            redacted_preview=result.redacted_preview,
        )

