"""Privacy-First Audit Logging Service for ContextShield."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.models.requests import SourceType
from backend.app.models.responses import Decision, LatencyStats, ThreatFinding

logger = logging.getLogger("contextshield.audit")


class AuditService:
    """Audit service enforcing strict privacy-first security principles.
    
    Security Guarantees:
    - NEVER persists raw hostile input.
    - NEVER persists complete detected secrets or tokens.
    - NEVER persists full document or sanitized content by default.
    - Persists only content hash (SHA-256), cryptographic/threat metadata,
      decision metrics, and safe truncated previews.
    """

    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record_event(
        self,
        request_id: str,
        source_type: SourceType,
        content_hash: str,
        decision: Decision,
        risk_score: float,
        findings: List[ThreatFinding],
        matched_policy_ids: List[str],
        latency: LatencyStats,
        sanitized_content: Optional[str] = None,
        llm_status: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Creates and stores a privacy-minimized audit entry."""
        
        # Build safe redacted preview from findings or summary
        if findings:
            redacted_preview = "; ".join(f"{f.rule_id}: {f.redacted_preview}" for f in findings[:3])
        else:
            redacted_preview = "No threat findings"

        # Truncate sanitized preview to max 80 characters if present
        sanitized_preview = None
        if sanitized_content:
            sanitized_preview = (
                sanitized_content[:80] + "..." if len(sanitized_content) > 80 else sanitized_content
            )

        record: Dict[str, Any] = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_type": source_type.value if hasattr(source_type, "value") else str(source_type),
            "content_hash": content_hash,
            "decision": decision.value if hasattr(decision, "value") else str(decision),
            "risk_score": risk_score,
            "threat_categories": list({f.category.value for f in findings}),
            "triggered_rule_ids": [f.rule_id for f in findings],
            "matched_policy_ids": matched_policy_ids,
            "latency_metrics": latency.model_dump() if hasattr(latency, "model_dump") else dict(latency),
            "redacted_preview": redacted_preview,
            "sanitized_preview": sanitized_preview,
        }

        # Privacy invariant: Store only metadata, prompt version/hash, and status; NEVER raw prompts or bodies
        if llm_status is not None:
            record["llm"] = {
                "provider": getattr(llm_status, "provider", None),
                "status": getattr(llm_status, "status", str(llm_status)),
                "model": getattr(llm_status, "model", None),
                "prompt_version": getattr(llm_status, "prompt_version", None),
                "prompt_hash": getattr(llm_status, "prompt_hash", None),
                "called": getattr(llm_status, "called", False),
                "reason_called": getattr(llm_status, "reason_called", None),
                "target_latency_ms": getattr(llm_status, "target_latency_ms", 800.0),
                "hard_timeout_ms": getattr(llm_status, "hard_timeout_ms", 1500.0),
                "target_exceeded": getattr(llm_status, "target_exceeded", None),
                "provider_request_id": getattr(llm_status, "provider_request_id", None),
            }

        self._records.append(record)
        logger.info(
            "Audit event: request_id=%s decision=%s risk_score=%.1f rules=%s",
            request_id,
            record["decision"],
            risk_score,
            record["triggered_rule_ids"]
        )
        return record

    def get_records(self) -> List[Dict[str, Any]]:
        """Returns in-memory audit records (useful for verification and testing)."""
        return list(self._records)

    def clear(self) -> None:
        """Clears in-memory audit logs."""
        self._records.clear()


# Global audit singleton
audit_service = AuditService()
