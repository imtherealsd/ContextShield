"""Storage abstraction package for ContextShield audit and telemetry."""

from typing import Optional
from backend.app.core.config import get_settings
from backend.app.storage.base import AuditStore
from backend.app.storage.memory import MemoryAuditStore
from backend.app.storage.postgres import PostgresAuditStore

_global_store: Optional[AuditStore] = None


def get_audit_store(force_new: bool = False) -> AuditStore:
    """Storage factory returning the configured AuditStore based on application settings.
    
    Defaults to MemoryAuditStore. When AUDIT_STORE=postgres, requires DATABASE_URL
    and instantiates PostgresAuditStore. Does not silently fall back.
    """
    global _global_store
    if _global_store is not None and not force_new:
        return _global_store

    settings = get_settings()
    store_type = settings.AUDIT_STORE.lower().strip()

    if store_type == "memory":
        _global_store = MemoryAuditStore()
        return _global_store

    elif store_type == "postgres":
        db_url = settings.get_database_url()
        if not db_url:
            raise RuntimeError(
                "AUDIT_STORE is set to 'postgres' but DATABASE_URL is not configured. "
                "Provide a valid PostgreSQL connection string or set AUDIT_STORE='memory'."
            )
        _global_store = PostgresAuditStore(database_url=db_url)
        return _global_store

    else:
        raise ValueError(
            f"Unsupported AUDIT_STORE '{store_type}'. Valid options are 'memory' or 'postgres'."
        )


def reset_global_store() -> None:
    """Reset the global store singleton (primarily for test harnesses)."""
    global _global_store
    _global_store = None


__all__ = [
    "AuditStore",
    "MemoryAuditStore",
    "PostgresAuditStore",
    "get_audit_store",
    "reset_global_store",
]
