"""Centralized Validated Configuration Management for ContextShield.

Enforces production-grade validation, strict typing, and secret redaction
via Pydantic Settings.
"""

from functools import lru_cache
from typing import Literal, Optional
from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production configuration model for ContextShield."""

    model_config = SettingsConfigDict(
        # pydantic-settings loads later dotenv files over earlier ones while
        # real environment variables remain higher precedence.
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Moss Semantic Retrieval Configuration
    MOSS_PROJECT_ID: Optional[str] = None
    MOSS_PROJECT_KEY: Optional[SecretStr] = None
    MOSS_INDEX_NAME: str = "contextshield-security"
    MOSS_HIGH_CONFIDENCE_SCORE: float = 0.90
    MOSS_SUPPORTING_SCORE: float = 0.80

    # Gemini & LLM Evaluator Configuration
    GEMINI_API_KEY: Optional[SecretStr] = None
    GEMINI_MODEL: str = "gemini-3.6-flash"
    LLM_PROVIDER: str = "gemini"
    LLM_TARGET_LATENCY_MS: float = 800.0
    LLM_HARD_TIMEOUT_MS: float = 1500.0
    LLM_PRIMARY_TIMEOUT_MS: Optional[float] = None

    # Storage & Persistence Configuration
    AUDIT_STORE: Literal["memory", "postgres"] = "memory"
    DATABASE_URL: Optional[SecretStr] = None

    # LiveKit Voice & Edge Agent Configuration
    LIVEKIT_URL: Optional[str] = None
    LIVEKIT_API_KEY: Optional[SecretStr] = None
    LIVEKIT_API_SECRET: Optional[SecretStr] = None
    LIVEKIT_STT_MODEL: str = "deepgram/nova-3"
    LIVEKIT_STT_LANGUAGE: str = "en"

    # Gateway Server Network Configuration
    CONTEXTSHIELD_API_URL: str = "http://127.0.0.1:8000"
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    @field_validator("LLM_TARGET_LATENCY_MS", "LLM_HARD_TIMEOUT_MS", "LLM_PRIMARY_TIMEOUT_MS")
    @classmethod
    def validate_latency(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("Latency timeouts must be strictly positive numbers.")
        return v

    @field_validator("MOSS_HIGH_CONFIDENCE_SCORE", "MOSS_SUPPORTING_SCORE")
    @classmethod
    def validate_scores(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence scores must be between 0.0 and 1.0.")
        return v

    @model_validator(mode="after")
    def validate_storage_settings(self) -> "Settings":
        if self.AUDIT_STORE == "postgres":
            if not self.DATABASE_URL or not self.DATABASE_URL.get_secret_value().strip():
                raise ValueError(
                    "DATABASE_URL must be configured when AUDIT_STORE='postgres'. "
                    "Provide a valid PostgreSQL connection string or set AUDIT_STORE='memory'."
                )
        return self

    # Safe accessors for unmasked values when required by external client SDKs
    def get_gemini_api_key(self) -> Optional[str]:
        return self.GEMINI_API_KEY.get_secret_value() if self.GEMINI_API_KEY else None

    def get_moss_project_key(self) -> Optional[str]:
        return self.MOSS_PROJECT_KEY.get_secret_value() if self.MOSS_PROJECT_KEY else None

    def get_database_url(self) -> Optional[str]:
        return self.DATABASE_URL.get_secret_value() if self.DATABASE_URL else None

    def get_livekit_api_secret(self) -> Optional[str]:
        return self.LIVEKIT_API_SECRET.get_secret_value() if self.LIVEKIT_API_SECRET else None

    def get_livekit_api_key(self) -> Optional[str]:
        return self.LIVEKIT_API_KEY.get_secret_value() if self.LIVEKIT_API_KEY else None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Returns the cached global application settings singleton."""
    return Settings()
