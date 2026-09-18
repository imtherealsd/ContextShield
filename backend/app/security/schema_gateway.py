"""Schema-Enforced Input Gateway for ContextShield."""

import hashlib
import re
from dataclasses import dataclass
from typing import Optional
from backend.app.models.requests import IngestRequest, SourceType


# Regex pattern to identify zero-width or hidden directional control characters used for evasion
ZERO_WIDTH_PATTERN = re.compile(r"[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E]")


@dataclass(frozen=True)
class GatewayContext:
    """Encapsulated gateway payload.
    
    Attributes:
        original_content: Untrusted external content preserved in original form (memory-only).
        normalized_content: Analysis copy with hidden control/zero-width chars removed for canonical analysis.
        source_type: Ingestion channel.
        agent_id: Target agent ID if specified.
        content_hash: SHA-256 hex digest for audit and deduplication without raw persistence.
        has_zero_width_chars: Boolean indicating presence of zero-width obfuscation characters.
    """
    original_content: str
    normalized_content: str
    source_type: SourceType
    agent_id: Optional[str]
    content_hash: str
    has_zero_width_chars: bool


class SchemaGateway:
    """Validates and processes input payloads before entering the security core."""

    @staticmethod
    def process(request: IngestRequest) -> GatewayContext:
        """Processes and inspects an IngestRequest into a dual-buffer GatewayContext.
        
        Crucial security principle: Does NOT silently discard or erase zero-width
        Unicode characters from original_content. Preserves evidence transiently in memory
        while creating a normalized_content copy for canonical threat detection.
        """
        raw_text = request.content
        
        # Check for zero-width / hidden characters
        has_zero_width = bool(ZERO_WIDTH_PATTERN.search(raw_text))
        
        # Create normalized analysis copy: strip zero-width characters so patterns like
        # 'ig\\u200Bnore' resolve to 'ignore' during analysis
        normalized_text = ZERO_WIDTH_PATTERN.sub("", raw_text)
        
        # Compute SHA-256 hash of original input
        content_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
        
        return GatewayContext(
            original_content=raw_text,
            normalized_content=normalized_text,
            source_type=request.source_type,
            agent_id=request.agent_id,
            content_hash=content_hash,
            has_zero_width_chars=has_zero_width
        )

    @classmethod
    def from_text(
        cls,
        text: str,
        source_type: SourceType = SourceType.DOCUMENT,
        agent_id: Optional[str] = None
    ) -> GatewayContext:
        """Constructs a GatewayContext directly from raw text (useful for post-sanitization rescanning)."""
        has_zero_width = bool(ZERO_WIDTH_PATTERN.search(text))
        normalized_text = ZERO_WIDTH_PATTERN.sub("", text)
        content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return GatewayContext(
            original_content=text,
            normalized_content=normalized_text,
            source_type=source_type,
            agent_id=agent_id,
            content_hash=content_hash,
            has_zero_width_chars=has_zero_width
        )
