"""ContextShield API routes."""

from backend.app.api.health import router as health_router
from backend.app.api.ingest import router as ingest_router

__all__ = ["health_router", "ingest_router"]
