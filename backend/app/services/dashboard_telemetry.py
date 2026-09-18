"""Dashboard Telemetry Service for ContextShield.

Provides bounded, privacy-safe in-memory telemetry for LiveKit voice turns
and dashboard operational metrics.
"""

from collections import deque
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("contextshield.dashboard.telemetry")


class DashboardTelemetryService:
    """Bounded in-memory session telemetry store.
    
    Guarantees:
    - Bounded storage via deque(maxlen=...) to prevent memory leaks.
    - Stores ONLY privacy-safe, already-redacted metadata.
    - NEVER stores raw transcripts, audio, credentials, or secrets.
    - Non-security-critical: failures never affect ContextShield security decisions.
    """

    def __init__(self, max_voice_events: int = 200):
        self._voice_events: deque = deque(maxlen=max_voice_events)
        self._last_voice_event_at: Optional[str] = None

    def record_voice_event(self, event_data: Dict[str, Any]) -> None:
        """Best-effort recording of privacy-safe RoomSecurityEvent telemetry."""
        try:
            now_iso = datetime.now(timezone.utc).isoformat()
            self._last_voice_event_at = now_iso
            if "timestamp" not in event_data or not event_data["timestamp"]:
                event_data["timestamp"] = now_iso
            self._voice_events.appendleft(event_data)
        except Exception as exc:
            logger.warning("Failed to record dashboard voice event (non-critical): %s", exc)

    def get_voice_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Returns the most recent bounded voice security events."""
        return list(self._voice_events)[:limit]

    def get_last_voice_event_at(self) -> Optional[str]:
        """Returns the ISO timestamp of the most recent voice turn, or None."""
        return self._last_voice_event_at

    def clear(self) -> None:
        """Clears voice telemetry (useful in test harnesses)."""
        self._voice_events.clear()
        self._last_voice_event_at = None


dashboard_telemetry = DashboardTelemetryService()
