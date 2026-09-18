"""Health check API router for ContextShield."""

from fastapi import APIRouter
from backend.app.models.responses import HealthResponse, MossHealthStatus
from backend.app.services.moss_service import moss_retriever

router = APIRouter(prefix="/v1/shield", tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Returns gateway health status and Moss local runtime state.
    
    Exposes:
    - status: "ok"
    - moss.status: "not_configured" | "loading" | "ready" | "error"
    - moss.loaded: true | false
    - moss.index_name: "contextshield-security" (or null when unconfigured)
    Never exposes project keys or credentials.
    """
    moss_info = moss_retriever.get_status()
    return HealthResponse(
        status="ok",
        moss=MossHealthStatus(
            status=moss_info.get("status", "not_configured"),
            loaded=moss_info.get("loaded", False),
            index_name=moss_info.get("index_name"),
        )
    )
