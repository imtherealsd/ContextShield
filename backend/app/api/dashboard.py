"""Read-Only Dashboard Telemetry API Router for ContextShield.

Provides truth-in-telemetry observability endpoints for the Next.js frontend:
- Stats derived strictly from real in-memory session records.
- Privacy-safe events with zero raw transcripts or secret leaks.
- Real Moss policy catalog read dynamically from security_policies.json.
- Verifiable runtime health derived from actual operational status.
"""

from datetime import datetime, timezone, timedelta
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from backend.app.services.audit import audit_service
from backend.app.services.dashboard_telemetry import dashboard_telemetry
from backend.app.services.evaluator import evaluator_service
from backend.app.services.moss_service import moss_retriever

logger = logging.getLogger("contextshield.dashboard.api")

router = APIRouter(prefix="/v1/shield/dashboard", tags=["Dashboard"])

POLICIES_PATH = Path(__file__).resolve().parent.parent / "data" / "security_policies.json"


@router.get("/stats")
async def get_dashboard_stats() -> Dict[str, Any]:
    """Returns aggregated metrics computed strictly from current in-memory session events."""
    audit_records = audit_service.get_records()
    voice_records = dashboard_telemetry.get_voice_events(limit=500)
    
    total_evaluated = len(audit_records)
    
    safe_count = 0
    sanitize_count = 0
    review_count = 0
    block_count = 0
    
    risk_scores: List[float] = []
    scanner_times: List[float] = []
    moss_times: List[float] = []
    total_times: List[float] = []
    gemini_called_count = 0
    gemini_skipped_count = 0
    
    for r in audit_records:
        dec = r.get("decision", "")
        if dec == "SAFE":
            safe_count += 1
        elif dec == "SANITIZE":
            sanitize_count += 1
        elif dec == "REVIEW":
            review_count += 1
        elif dec == "BLOCK":
            block_count += 1
            
        risk = r.get("risk_score")
        if risk is not None:
            risk_scores.append(float(risk))
            
        lat = r.get("latency_metrics", {})
        if "scanner_ms" in lat and lat["scanner_ms"] is not None:
            scanner_times.append(float(lat["scanner_ms"]))
        if "moss_ms" in lat and lat["moss_ms"] is not None:
            moss_times.append(float(lat["moss_ms"]))
        if "total_ms" in lat and lat["total_ms"] is not None:
            total_times.append(float(lat["total_ms"]))
            
        llm = r.get("llm", {})
        if llm.get("called", False):
            gemini_called_count += 1
        else:
            gemini_skipped_count += 1

    # Voice to decision times
    voice_to_dec_times: List[float] = [
        float(v["voice_to_decision_ms"])
        for v in voice_records
        if v.get("voice_to_decision_ms") is not None
    ]

    safe_pct = round((safe_count / total_evaluated * 100.0), 1) if total_evaluated > 0 else 0.0
    sanitize_pct = round((sanitize_count / total_evaluated * 100.0), 1) if total_evaluated > 0 else 0.0
    review_pct = round((review_count / total_evaluated * 100.0), 1) if total_evaluated > 0 else 0.0
    block_pct = round((block_count / total_evaluated * 100.0), 1) if total_evaluated > 0 else 0.0
    
    gemini_invocation_rate = round((gemini_called_count / total_evaluated * 100.0), 1) if total_evaluated > 0 else 0.0
    gemini_skip_rate = round((gemini_skipped_count / total_evaluated * 100.0), 1) if total_evaluated > 0 else 100.0

    return {
        "session_label": "Current Session (in-memory)",
        "is_session_data": True,
        "total_evaluated": total_evaluated,
        "safe_count": safe_count,
        "sanitize_count": sanitize_count,
        "review_count": review_count,
        "block_count": block_count,
        "safe_pct": safe_pct,
        "sanitize_pct": sanitize_pct,
        "review_pct": review_pct,
        "block_pct": block_pct,
        "average_risk_score": round(sum(risk_scores) / len(risk_scores), 1) if risk_scores else None,
        "average_scanner_ms": round(sum(scanner_times) / len(scanner_times), 2) if scanner_times else None,
        "average_moss_ms": round(sum(moss_times) / len(moss_times), 2) if moss_times else None,
        "average_total_ms": round(sum(total_times) / len(total_times), 2) if total_times else None,
        "average_voice_to_decision_ms": round(sum(voice_to_dec_times) / len(voice_to_dec_times), 2) if voice_to_dec_times else None,
        "gemini_called_count": gemini_called_count,
        "gemini_skipped_count": gemini_skipped_count,
        "gemini_invocation_rate": gemini_invocation_rate,
        "gemini_skip_rate": gemini_skip_rate,
        "voice_turns_count": len(voice_records),
    }


@router.get("/events")
async def get_dashboard_events(
    limit: int = Query(50, ge=1, le=200),
    source: Optional[str] = None,
    decision: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Returns recent privacy-safe security events with filtering support."""
    audit_records = audit_service.get_records()
    voice_records = {v.get("request_id"): v for v in dashboard_telemetry.get_voice_events(limit=200)}

    unified_events: List[Dict[str, Any]] = []

    # Process in reverse chronological order
    for r in reversed(audit_records):
        src = r.get("source_type", "unknown")
        dec = r.get("decision", "UNKNOWN")

        # Filters
        if source and source.lower() != "all" and src.lower() != source.lower():
            continue
        if decision and decision.upper() != "ALL" and dec.upper() != decision.upper():
            continue

        req_id = r.get("request_id")
        voice_meta = voice_records.get(req_id, {})

        approved_ctx_available = (dec == "SAFE" or dec == "SANITIZE")

        lat = dict(r.get("latency_metrics", {}))
        if voice_meta.get("voice_to_decision_ms") is not None:
            lat["voice_to_decision_ms"] = voice_meta["voice_to_decision_ms"]

        event_entry: Dict[str, Any] = {
            "request_id": req_id,
            "turn_id": voice_meta.get("turn_id"),
            "timestamp": r.get("timestamp"),
            "source": src,
            "decision": dec,
            "risk_score": r.get("risk_score", 0.0),
            "threat_categories": r.get("threat_categories", []),
            "triggered_rule_ids": r.get("triggered_rule_ids", []),
            "matched_policy_ids": r.get("matched_policy_ids", []),
            "latency": lat,
            "redacted_preview": r.get("redacted_preview", ""),
            "sanitized_preview": r.get("sanitized_preview"),
            "approved_context_available": approved_ctx_available,
            "participant_identity": voice_meta.get("participant_identity"),
            "room_name": voice_meta.get("room_name"),
            "llm": r.get("llm"),
        }
        unified_events.append(event_entry)

        if len(unified_events) >= limit:
            break

    return unified_events


@router.get("/voice-turns")
async def get_dashboard_voice_turns(limit: int = Query(50, ge=1, le=200)) -> List[Dict[str, Any]]:
    """Returns bounded voice events specifically captured from LiveKit Cloud rooms."""
    return dashboard_telemetry.get_voice_events(limit=limit)


@router.get("/policies")
async def get_dashboard_policies() -> Dict[str, Any]:
    """Returns the real security policy registry dynamically read from security_policies.json."""
    policies_data: List[Dict[str, Any]] = []
    if POLICIES_PATH.exists():
        try:
            with open(POLICIES_PATH, "r", encoding="utf-8") as f:
                raw_policies = json.load(f)
            for p in raw_policies:
                policies_data.append({
                    "id": p.get("id"),
                    "category": p.get("metadata", {}).get("category"),
                    "severity": p.get("metadata", {}).get("severity"),
                    "recommended_action": p.get("metadata", {}).get("recommended_action"),
                    "policy_version": p.get("metadata", {}).get("policy_version", "1.0.0"),
                    "text": p.get("text"),
                })
        except Exception as exc:
            logger.error("Failed to read security_policies.json: %s", exc)

    moss_status = moss_retriever.get_status()

    return {
        "total_policies": len(policies_data),
        "moss_index_name": moss_status.get("index_name"),
        "moss_status": moss_status.get("status", "not_configured"),
        "moss_loaded": moss_status.get("loaded", False),
        "policies": policies_data,
    }


@router.get("/health")
async def get_dashboard_health() -> Dict[str, Any]:
    """Truthfully derived runtime evidence of all connected subsystems."""
    moss_stat = moss_retriever.get_status()

    # Determine last Gemini status from audit events
    audit_records = audit_service.get_records()
    last_llm_status: Optional[str] = None
    for r in reversed(audit_records):
        llm = r.get("llm")
        if llm and "status" in llm:
            last_llm_status = llm["status"]
            break

    # Determine LiveKit recent activity
    last_voice_at = dashboard_telemetry.get_last_voice_event_at()
    recent_voice_activity: bool = False
    if last_voice_at:
        try:
            dt = datetime.fromisoformat(last_voice_at.replace("Z", "+00:00"))
            recent_voice_activity = (datetime.now(timezone.utc) - dt) < timedelta(minutes=5)
        except Exception:
            recent_voice_activity = False

    return {
        "gateway": "healthy",
        "session_events_count": len(audit_records),
        "moss": {
            "status": moss_stat.get("status", "not_configured"),
            "loaded": moss_stat.get("loaded", False),
            "index_name": moss_stat.get("index_name"),
        },
        "gemini": {
            "configured": evaluator_service.configured,
            "model": evaluator_service.model if evaluator_service.configured else None,
            "last_status": last_llm_status or ("not_called" if evaluator_service.configured else "not_configured"),
        },
        "livekit": {
            "last_voice_event_at": last_voice_at,
            "recent_activity": recent_voice_activity,
        },
    }


@router.post("/telemetry/voice-turn")
async def record_voice_turn_telemetry(payload: Dict[str, Any]) -> Dict[str, str]:
    """Receives non-security-critical safe voice turn telemetry from LiveKit worker."""
    safe_data = {
        "turn_id": payload.get("turn_id"),
        "room_name": payload.get("room_name"),
        "participant_identity": payload.get("participant_identity"),
        "request_id": payload.get("request_id"),
        "source": "livekit_voice",
        "decision": payload.get("decision", "BLOCK"),
        "risk_score": payload.get("risk_score", 100.0),
        "threat_categories": payload.get("threat_categories", []),
        "matched_policy_ids": payload.get("matched_policy_ids", []),
        "moss_ms": payload.get("moss_ms"),
        "llm_called": payload.get("llm_called", False),
        "llm_status": payload.get("llm_status"),
        "shield_total_ms": payload.get("shield_total_ms", 0.0),
        "voice_to_decision_ms": payload.get("voice_to_decision_ms"),
        "redacted_preview": payload.get("redacted_preview"),
        "approved_context_available": payload.get("approved_context_available", False),
        "timestamp": payload.get("timestamp") or datetime.now(timezone.utc).isoformat(),
    }
    dashboard_telemetry.record_voice_event(safe_data)
    return {"status": "ok"}

