"""ContextShield FastAPI Application Entrypoint.

YC Fall 2026 x Moss Zero Latency Builder Sprint — Milestone 1: Security Core.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.demo import router as demo_router
from backend.app.api.health import router as health_router
from backend.app.api.ingest import router as ingest_router
from backend.app.services.moss_service import moss_retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    # Attempt Moss client initialization (status will be 'not_configured' if env vars missing)
    await moss_retriever.initialize()
    yield
    # Teardown logic if needed


def create_app() -> FastAPI:
    """Factory creating configured FastAPI instance."""
    app = FastAPI(
        title="ContextShield Security Gateway",
        description=(
            "Real-time low-latency security gateway validating untrusted external "
            "context before reaching AI agents."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Schema-enforced input gateway: strict validation error formatting
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "SchemaValidationError",
                "message": "Malformed or unexpected input structure rejected by schema gateway.",
                "details": exc.errors(),
            },
        )

    # Register Routers
    app.include_router(health_router)
    app.include_router(ingest_router)
    app.include_router(dashboard_router)
    app.include_router(demo_router)

    return app


app = create_app()
