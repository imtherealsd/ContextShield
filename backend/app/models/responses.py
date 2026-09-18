"""Response models for ContextShield."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class Decision(str, Enum):
    """ContextShield security decisions."""
    SAFE = "SAFE"
    SANITIZE = "SANITIZE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


class ThreatCategory(str, Enum):
    """Detected threat classifications."""
    INSTRUCTION_OVERRIDE = "instruction_override"
    SYSTEM_PROMPT_EXTRACTION = "system_prompt_extraction"
    CREDENTIAL_EXFILTRATION = "credential_exfiltration"
    UNAUTHORIZED_TRANSMISSION = "unauthorized_transmission"
    ROLE_MANIPULATION = "role_manipulation"


class Severity(str, Enum):
    """Threat severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ThreatFinding(BaseModel):
    """Structured threat finding with redacted secrets."""
    rule_id: str = Field(..., description="Unique deterministic rule identifier.")
    category: ThreatCategory = Field(..., description="Category of threat detected.")
    severity: Severity = Field(..., description="Severity level of the threat.")
    start_offset: int = Field(..., description="Character start offset in analysis buffer.")
    end_offset: int = Field(..., description="Character end offset in analysis buffer.")
    redacted_preview: str = Field(
        ...,
        description="Safe preview of matched pattern with all secrets and tokens redacted."
    )
    description: str = Field(..., description="Human-readable description of detected threat.")


class LLMRiskEvaluation(BaseModel):
    """Strict structured output schema returned by the contextual LLM evaluator."""
    decision: Decision = Field(..., description="Evaluator security decision: SAFE, SANITIZE, REVIEW, BLOCK.")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Assessed risk score from 0.0 to 100.0.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Evaluator confidence from 0.0 to 1.0.")
    threat_categories: List[str] = Field(default_factory=list, description="Identified threat categories.")
    matched_policy_ids: List[str] = Field(default_factory=list, description="Relevant Moss security policy IDs.")
    hostile_segments: List[str] = Field(default_factory=list, description="Identified hostile spans or segments.")
    sanitization_possible: bool = Field(..., description="Whether hostile spans can be cleanly sanitized.")
    reason: str = Field(..., description="Short explanation of the evaluation decision.")

    @field_validator("threat_categories", mode="after")
    @classmethod
    def validate_categories(cls, cats: List[Any]) -> List[str]:
        supported = {c.value for c in ThreatCategory}
        valid = []
        for c in cats:
            val = c.value if isinstance(c, ThreatCategory) else str(c)
            if val in supported:
                valid.append(val)
        return valid


class LLMIngestStatus(BaseModel):
    """Explicit LLM evaluator state included with ingestion responses."""
    provider: Optional[str] = Field(default="gemini", description="Active LLM provider: gemini.")
    status: str = Field(
        ...,
        description="LLM status: not_called, success, timeout, rate_limited, api_error, schema_error, refusal, not_configured, model_unavailable, invalid_provider."
    )
    model: Optional[str] = Field(default=None, description="Configured or executed LLM model identifier.")
    prompt_version: str = Field(default="contextshield-risk-v1", description="Immutable prompt version identifier.")
    prompt_hash: str = Field(..., description="SHA-256 hash of immutable system prompt.")
    called: bool = Field(..., description="Whether contextual LLM evaluation was executed.")
    reason_called: Optional[str] = Field(default=None, description="Reason LLM was invoked (e.g. ambiguous_context).")
    target_latency_ms: Optional[float] = Field(default=800.0, description="Target evaluation latency in milliseconds.")
    hard_timeout_ms: Optional[float] = Field(default=1500.0, description="Hard deadline timeout in milliseconds.")
    target_exceeded: Optional[bool] = Field(default=None, description="Whether actual evaluation latency exceeded target latency.")
    provider_request_id: Optional[str] = Field(default=None, description="Provider API request ID when available.")
    invalid_llm_policy_ids_count: int = Field(default=0, description="Count of hallucinated policy IDs discarded from LLM output.")


class LatencyStats(BaseModel):
    """Execution latency measurements in milliseconds."""
    scanner_ms: float = Field(..., description="Actual deterministic scanner latency in milliseconds.")
    moss_ms: Optional[float] = Field(
        default=None,
        description="Actual Moss retrieval latency in milliseconds, or null if unexecuted."
    )
    llm_ms: Optional[float] = Field(
        default=None,
        description="Actual contextual LLM evaluator latency in milliseconds, or null if unexecuted."
    )
    total_ms: float = Field(..., description="Total pipeline execution latency in milliseconds.")


class MossPolicyMatch(BaseModel):
    """Structured match retrieved from the Moss local runtime index."""
    id: str = Field(..., description="Unique policy document identifier (e.g. POL-001).")
    text: str = Field(..., description="Full text of the matched policy.")
    score: float = Field(..., description="Relevance similarity score (0.0 to 1.0).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Policy metadata attributes.")
    category: Optional[str] = Field(default=None, description="Extracted category from metadata.")
    severity: Optional[str] = Field(default=None, description="Extracted severity from metadata.")
    recommended_action: Optional[str] = Field(default=None, description="Recommended action (BLOCK, SANITIZE, REVIEW).")


class MossIngestStatus(BaseModel):
    """Explicit Moss state included with ingestion responses."""
    status: str = Field(..., description="Moss connection status: not_configured, loading, ready, error.")
    loaded: bool = Field(..., description="Whether security policy index is loaded.")
    query_executed: bool = Field(..., description="Whether a real Moss query was executed.")
    index_name: Optional[str] = Field(default=None, description="Active Moss policy index name.")
    result_count: int = Field(default=0, description="Number of matched policy documents returned.")


class IngestResponse(BaseModel):
    """Response returned by the /v1/shield/ingest endpoint."""
    request_id: str = Field(..., description="Unique UUID for this ingestion request.")
    decision: Decision = Field(..., description="Final security decision.")
    risk_score: float = Field(..., ge=0.0, le=100.0, description="Calculated risk score from 0 to 100.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score from 0.0 to 1.0.")
    detected_threats: List[ThreatFinding] = Field(
        default_factory=list,
        description="List of structured threat findings."
    )
    matched_policy_ids: List[str] = Field(
        default_factory=list,
        description="Identifiers of matched ContextShield security policies from Moss."
    )
    sanitized_content: Optional[str] = Field(
        default=None,
        description="Sanitized version of context if decision is SANITIZE, otherwise null."
    )
    agent_context: Optional[str] = Field(
        default=None,
        description="Safe context delivered to protected agent (populated ONLY for SAFE or SANITIZE)."
    )
    moss: MossIngestStatus = Field(..., description="Explicit Moss integration state.")
    llm: LLMIngestStatus = Field(..., description="Explicit LLM evaluator state.")
    latency: LatencyStats = Field(..., description="High-resolution latency breakdown.")


class MossHealthStatus(BaseModel):
    """Moss Local Runtime status for /health."""
    status: str = Field(..., description="Moss connection or configuration status.")
    loaded: bool = Field(..., description="Whether security policy index is loaded.")
    index_name: Optional[str] = Field(default=None, description="Active Moss index name.")


class HealthResponse(BaseModel):
    """Response returned by /v1/shield/health."""
    status: str = Field(default="ok", description="Overall gateway health status.")
    moss: MossHealthStatus = Field(..., description="Moss local runtime status.")
