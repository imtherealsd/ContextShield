"""Unit and contract tests for ContextShield Audit Storage Abstraction."""

from datetime import datetime, timezone
import os
from unittest.mock import patch
import pytest
from backend.app.core.config import Settings
from backend.app.storage import (
    AuditStore,
    MemoryAuditStore,
    PostgresAuditStore,
    get_audit_store,
    reset_global_store,
)


def _make_sample_record(req_id: str = "req-100", decision: str = "SAFE") -> dict:
    return {
        "request_id": req_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_type": "api",
        "content_hash": "a" * 64,
        "decision": decision,
        "risk_score": 0.0 if decision == "SAFE" else 100.0,
        "threat_categories": [] if decision == "SAFE" else ["INSTRUCTION_OVERRIDE"],
        "triggered_rule_ids": [] if decision == "SAFE" else ["RULE-IO-001"],
        "matched_policy_ids": [] if decision == "SAFE" else ["POL-001"],
        "latency_metrics": {"scanner_ms": 0.5, "moss_ms": 1.2, "total_ms": 1.7},
        "redacted_preview": "Safe context preview" if decision == "SAFE" else "RULE-IO-001: ***REDACTED***",
        "sanitized_preview": None,
        "llm": None,
    }


@pytest.mark.asyncio
async def test_memory_store_contract():
    """Validates MemoryAuditStore operations: record, get, limit, clear."""
    store = MemoryAuditStore(max_records=5)
    assert not store.is_persistent

    rec1 = _make_sample_record("req-1", "SAFE")
    rec2 = _make_sample_record("req-2", "BLOCK")
    rec3 = _make_sample_record("req-3", "SANITIZE")

    await store.record_event(rec1)
    await store.record_event(rec2)
    await store.record_event(rec3)

    records = await store.get_records()
    assert len(records) == 3
    assert records[0]["request_id"] == "req-1"
    assert records[1]["request_id"] == "req-2"
    assert records[2]["request_id"] == "req-3"

    # Test limit
    recent = await store.get_records(limit=2)
    assert len(recent) == 2
    assert recent[0]["request_id"] == "req-2"
    assert recent[1]["request_id"] == "req-3"

    # Test clear
    await store.clear()
    assert len(await store.get_records()) == 0


@pytest.mark.asyncio
async def test_storage_contract_with_sqlite_engine():
    """Fast async storage contract test using SQLite, not PostgreSQL integration."""
    store = PostgresAuditStore(database_url="sqlite+aiosqlite:///:memory:")
    assert store.is_persistent
    await store.create_tables()

    rec1 = _make_sample_record("req-pg-1", "SAFE")
    rec2 = _make_sample_record("req-pg-2", "BLOCK")

    await store.record_event(rec1)
    await store.record_event(rec2)

    records = await store.get_records()
    assert len(records) == 2
    assert records[0]["request_id"] == "req-pg-1"
    assert records[0]["decision"] == "SAFE"
    assert records[0]["latency_metrics"]["total_ms"] == 1.7
    assert records[1]["request_id"] == "req-pg-2"
    assert records[1]["decision"] == "BLOCK"
    assert "RULE-IO-001" in records[1]["triggered_rule_ids"]

    # Test limit
    recent = await store.get_records(limit=1)
    assert len(recent) == 1
    assert recent[0]["request_id"] == "req-pg-2"

    # Test clear
    await store.clear()
    assert len(await store.get_records()) == 0
    await store.dispose()


def test_postgres_url_is_normalized_to_asyncpg():
    """Provider-style PostgreSQL URLs retain the asyncpg driver."""
    store = PostgresAuditStore("postgresql://user:password@localhost:5432/contextshield")
    assert store.database_url == "postgresql+asyncpg://user:password@localhost:5432/contextshield"
    assert store.engine.url.drivername == "postgresql+asyncpg"


def test_postgres_store_empty_url_rejected():
    """PostgresAuditStore rejects empty database URLs."""
    with pytest.raises(ValueError):
        PostgresAuditStore(database_url="")


def test_get_audit_store_factory_memory_default():
    """Factory returns MemoryAuditStore by default."""
    reset_global_store()
    with patch.dict(os.environ, {"AUDIT_STORE": "memory"}, clear=False):
        store = get_audit_store(force_new=True)
        assert isinstance(store, MemoryAuditStore)
        assert not store.is_persistent


def test_get_audit_store_factory_postgres_requires_database_url():
    """Factory raises error when AUDIT_STORE=postgres but DATABASE_URL is not set."""
    reset_global_store()
    with patch("backend.app.storage.get_settings") as mock_get_settings:
        mock_settings = Settings(
            _env_file=None,
            AUDIT_STORE="memory",  # Mock valid Pydantic setting
        )
        # Simulate someone bypassing Pydantic or changing store_type
        mock_settings.AUDIT_STORE = "postgres"
        mock_get_settings.return_value = mock_settings

        with pytest.raises(RuntimeError) as excinfo:
            get_audit_store(force_new=True)
        assert "DATABASE_URL is not configured" in str(excinfo.value)
    reset_global_store()


def test_get_audit_store_factory_unsupported_type_raises():
    """Factory raises ValueError for unknown store types."""
    reset_global_store()
    with patch("backend.app.storage.get_settings") as mock_get_settings:
        mock_settings = Settings(_env_file=None)
        mock_settings.AUDIT_STORE = "dynamodb"  # type: ignore[assignment]
        mock_get_settings.return_value = mock_settings

        with pytest.raises(ValueError) as excinfo:
            get_audit_store(force_new=True)
        assert "Unsupported AUDIT_STORE" in str(excinfo.value)
    reset_global_store()
