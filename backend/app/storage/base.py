"""Base storage abstraction interface for ContextShield audit telemetry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AuditStore(ABC):
    """Abstract interface defining the contract for ContextShield audit storage.
    
    Guarantees:
    - Strictly privacy-safe audit records.
    - Zero raw hostile payloads or secret credentials.
    """

    @property
    @abstractmethod
    def is_persistent(self) -> bool:
        """Whether this store persists records to an external persistent database."""
        pass

    @abstractmethod
    def record_event(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a privacy-minimized audit record."""
        pass

    @abstractmethod
    def get_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve audit records in chronological order."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clears audit records (used for test isolation)."""
        pass

    async def record_event_async(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Async variant for non-blocking persistence where supported."""
        return self.record_event(record)

    async def get_records_async(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Async variant for non-blocking queries where supported."""
        return self.get_records(limit=limit)
