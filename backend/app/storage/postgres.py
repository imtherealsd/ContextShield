"""PostgreSQL persistent audit storage implementation for ContextShield.

Enforces production database persistence using SQLAlchemy 2.0 and asyncpg,
with strict privacy constraints (no raw hostile input or credentials persisted).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.app.storage.base import AuditStore

logger = logging.getLogger("contextshield.storage.postgres")

Base = declarative_base()


class AuditTelemetryModel(Base):
    """SQLAlchemy ORM model for privacy-safe audit telemetry."""

    __tablename__ = "audit_telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), index=True, nullable=False)
    source_type = Column(String(32), nullable=False)
    decision = Column(String(16), nullable=False)
    risk_score = Column(Float, nullable=False)
    content_hash = Column(String(64), nullable=False)
    threat_categories = Column(JSON, default=list, nullable=False)
    triggered_rule_ids = Column(JSON, default=list, nullable=False)
    matched_policy_ids = Column(JSON, default=list, nullable=False)
    latency_metrics = Column(JSON, default=dict, nullable=False)
    redacted_preview = Column(Text, default="", nullable=False)
    sanitized_preview = Column(Text, nullable=True)
    llm = Column(JSON, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ORM record to the standard ContextShield audit dictionary."""
        ts = self.timestamp.isoformat() if hasattr(self.timestamp, "isoformat") else str(self.timestamp)
        return {
            "request_id": self.request_id,
            "timestamp": ts,
            "source_type": self.source_type,
            "content_hash": self.content_hash,
            "decision": self.decision,
            "risk_score": float(self.risk_score),
            "threat_categories": list(self.threat_categories or []),
            "triggered_rule_ids": list(self.triggered_rule_ids or []),
            "matched_policy_ids": list(self.matched_policy_ids or []),
            "latency_metrics": dict(self.latency_metrics or {}),
            "redacted_preview": self.redacted_preview or "",
            "sanitized_preview": self.sanitized_preview,
            "llm": self.llm,
        }


class PostgresAuditStore(AuditStore):
    """PostgreSQL implementation of AuditStore with SQLAlchemy 2.0."""

    def __init__(self, database_url: str, echo: bool = False):
        if not database_url or not database_url.strip():
            raise ValueError("DATABASE_URL cannot be empty for PostgresAuditStore.")
        
        self.database_url = database_url.strip()
        # Ensure proper driver for sync engine if standard postgresql:// provided
        sync_url = self.database_url
        if sync_url.startswith("postgresql+asyncpg://"):
            sync_url = sync_url.replace("postgresql+asyncpg://", "postgresql://", 1)

        try:
            self.engine = create_engine(sync_url, echo=echo, pool_pre_ping=True)
            self.SessionFactory = sessionmaker(bind=self.engine)
            logger.info("PostgresAuditStore initialized.")
        except Exception as exc:
            logger.error("Failed to initialize database engine for PostgresAuditStore: %s", exc)
            raise

    @property
    def is_persistent(self) -> bool:
        return True

    def create_tables(self) -> None:
        """Helper to initialize database tables (e.g. for testing)."""
        Base.metadata.create_all(self.engine)

    def record_event(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a privacy-minimized audit record into PostgreSQL."""
        # Parse timestamp safely
        ts_val = record.get("timestamp")
        if isinstance(ts_val, str):
            try:
                ts = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
        elif isinstance(ts_val, datetime):
            ts = ts_val
        else:
            ts = datetime.now(timezone.utc)

        db_item = AuditTelemetryModel(
            request_id=record.get("request_id", ""),
            timestamp=ts,
            source_type=record.get("source_type", "api"),
            decision=record.get("decision", "BLOCK"),
            risk_score=float(record.get("risk_score", 0.0)),
            content_hash=record.get("content_hash", ""),
            threat_categories=record.get("threat_categories", []),
            triggered_rule_ids=record.get("triggered_rule_ids", []),
            matched_policy_ids=record.get("matched_policy_ids", []),
            latency_metrics=record.get("latency_metrics", {}),
            redacted_preview=record.get("redacted_preview", ""),
            sanitized_preview=record.get("sanitized_preview"),
            llm=record.get("llm"),
        )

        with self.SessionFactory() as session:
            session.add(db_item)
            session.commit()

        return record

    def get_records(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve audit records ordered chronologically."""
        with self.SessionFactory() as session:
            stmt = select(AuditTelemetryModel).order_by(AuditTelemetryModel.timestamp.asc())
            results = session.scalars(stmt).all()
            records = [r.to_dict() for r in results]
            if limit is not None and limit > 0:
                return records[-limit:]
            return records

    def clear(self) -> None:
        """Clear all audit records (primarily for test harnesses)."""
        with self.SessionFactory() as session:
            session.query(AuditTelemetryModel).delete()
            session.commit()
