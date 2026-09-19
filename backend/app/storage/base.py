"""Base storage abstraction interface for ContextShield audit telemetry."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AuditStorageError(RuntimeError):
    """Safe, implementation-agnostic error raised by audit persistence."""


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
    async def record_event(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a privacy-minimized audit record."""
        pass

    @abstractmethod
    async def get_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve audit records in chronological order."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Clears audit records (used for test isolation)."""
        pass
