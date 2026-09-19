"""In-memory audit storage implementation for ContextShield.

Provides zero-dependency, bounded in-memory telemetry suitable for local development,
test runners, and ephemeral demo environments.
"""

from collections import deque
import logging
from typing import Any, Dict, List, Optional
from backend.app.storage.base import AuditStore

logger = logging.getLogger("contextshield.storage.memory")


class MemoryAuditStore(AuditStore):
    """In-memory implementation of AuditStore.
    
    Guarantees:
    - Zero external database dependencies.
    - Preserves all existing in-memory telemetry contracts.
    """

    def __init__(self, max_records: int = 1000):
        self._max_records = max_records
        self._records: deque = deque(maxlen=max_records)

    @property
    def is_persistent(self) -> bool:
        return False

    def record_event(self, record: Dict[str, Any]) -> Dict[str, Any]:
        self._records.append(record)
        return record

    def get_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        records = list(self._records)
        if limit is not None and limit > 0:
            return records[-limit:]
        return records

    def clear(self) -> None:
        self._records.clear()
