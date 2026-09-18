"""Request models for ContextShield."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class SourceType(str, Enum):
    """Allowed ingestion source types."""
    WEB = "web"
    API = "api"
    DOCUMENT = "document"
    LIVEKIT_VOICE = "livekit_voice"


class IngestRequest(BaseModel):
    """Strict schema-enforced input gateway request model."""
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    content: str = Field(
        ...,
        min_length=1,
        max_length=500_000,
        description="Untrusted external context to be evaluated before reaching the AI agent."
    )
    source_type: SourceType = Field(
        ...,
        description="Source channel of the untrusted context."
    )
    agent_id: Optional[str] = Field(
        default=None,
        max_length=128,
        description="Optional identifier of the recipient protected agent."
    )
