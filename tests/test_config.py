"""Tests for Centralized Settings Management and Validation."""

import os
from unittest.mock import patch
import pytest
from pydantic import ValidationError
from backend.app.core.config import Settings


def test_settings_defaults():
    """Validates sensible defaults for non-secret values."""
    settings = Settings(
        _env_file=None,  # Do not read external env files for isolated test
        MOSS_PROJECT_ID=None,
        MOSS_PROJECT_KEY=None,
        GEMINI_API_KEY=None,
        DATABASE_URL=None,
        LIVEKIT_API_KEY=None,
        LIVEKIT_API_SECRET=None,
    )
    assert settings.AUDIT_STORE == "memory"
    assert settings.MOSS_INDEX_NAME == "contextshield-security"
    assert settings.GEMINI_MODEL == "gemini-3.6-flash"
    assert settings.LLM_TARGET_LATENCY_MS == 800.0
    assert settings.LLM_HARD_TIMEOUT_MS == 1500.0
    assert settings.MOSS_HIGH_CONFIDENCE_SCORE == 0.90
    assert settings.MOSS_SUPPORTING_SCORE == 0.80
    assert settings.LIVEKIT_STT_MODEL == "deepgram/nova-3"


def test_settings_secret_redaction():
    """Validates that secrets are wrapped in SecretStr and never exposed in str or repr."""
    fake_gemini_key = "AIzaSyTestFakeSecretKey123456789"
    fake_db_url = "postgresql://user:super_secret_pw@localhost:5432/shield_db"
    fake_livekit_key = "livekit_test_secret_key_123"

    settings = Settings(
        _env_file=None,
        GEMINI_API_KEY=fake_gemini_key,
        DATABASE_URL=fake_db_url,
        LIVEKIT_API_KEY=fake_livekit_key,
    )

    # 1. Repr and str representations must redact the secret
    repr_str = repr(settings)
    assert fake_gemini_key not in repr_str
    assert "super_secret_pw" not in repr_str
    assert fake_livekit_key not in repr_str
    assert "**********" in repr_str

    # 2. String representation of SecretStr field directly
    assert fake_gemini_key not in str(settings.GEMINI_API_KEY)
    assert "**********" in str(settings.GEMINI_API_KEY)

    # 3. Unmasked accessor provides actual value when required
    assert settings.get_gemini_api_key() == fake_gemini_key
    assert settings.get_database_url() == fake_db_url
    assert settings.get_livekit_api_key() == fake_livekit_key


def test_settings_invalid_latency_rejected():
    """Validates that non-positive latency values raise ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None, LLM_TARGET_LATENCY_MS=-100.0)
    assert "Latency timeouts must be strictly positive" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None, LLM_HARD_TIMEOUT_MS=0.0)
    assert "Latency timeouts must be strictly positive" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None, LLM_PRIMARY_TIMEOUT_MS=-1.0)
    assert "Latency timeouts must be strictly positive" in str(excinfo.value)


def test_settings_invalid_confidence_scores_rejected():
    """Validates that confidence scores outside [0.0, 1.0] raise ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None, MOSS_HIGH_CONFIDENCE_SCORE=1.5)
    assert "Confidence scores must be between 0.0 and 1.0" in str(excinfo.value)


def test_settings_postgres_requires_database_url():
    """Validates that AUDIT_STORE=postgres raises ValidationError if DATABASE_URL is missing."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None, AUDIT_STORE="postgres", DATABASE_URL=None)
    assert "DATABASE_URL must be configured when AUDIT_STORE='postgres'" in str(excinfo.value)

    # With valid DATABASE_URL, succeeds
    valid_settings = Settings(
        _env_file=None,
        AUDIT_STORE="postgres",
        DATABASE_URL="postgresql+asyncpg://user:pw@localhost/db",
    )
    assert valid_settings.AUDIT_STORE == "postgres"
    assert valid_settings.get_database_url() == "postgresql+asyncpg://user:pw@localhost/db"


def test_settings_environment_override():
    """Validates that environment variables override defaults correctly."""
    with patch.dict(
        os.environ,
        {
            "GEMINI_MODEL": "gemini-1.5-pro",
            "LLM_TARGET_LATENCY_MS": "950.0",
            "MOSS_INDEX_NAME": "custom-moss-index",
        },
    ):
        settings = Settings(_env_file=None)
        assert settings.GEMINI_MODEL == "gemini-1.5-pro"
        assert settings.LLM_TARGET_LATENCY_MS == 950.0
        assert settings.MOSS_INDEX_NAME == "custom-moss-index"


def test_settings_dotenv_precedence_and_environment_override(tmp_path, monkeypatch):
    """Real environment > .env.local > .env > defaults."""
    base_env = tmp_path / ".env"
    local_env = tmp_path / ".env.local"
    base_env.write_text(
        "GEMINI_MODEL=from-dotenv\nMOSS_INDEX_NAME=base-index\nLLM_TARGET_LATENCY_MS=700\n",
        encoding="utf-8",
    )
    local_env.write_text(
        "GEMINI_MODEL=from-local\nMOSS_INDEX_NAME=local-index\n",
        encoding="utf-8",
    )

    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.delenv("MOSS_INDEX_NAME", raising=False)
    monkeypatch.delenv("LLM_TARGET_LATENCY_MS", raising=False)
    settings = Settings(_env_file=(str(base_env), str(local_env)))
    assert settings.GEMINI_MODEL == "from-local"
    assert settings.MOSS_INDEX_NAME == "local-index"
    assert settings.LLM_TARGET_LATENCY_MS == 700.0

    monkeypatch.setenv("GEMINI_MODEL", "from-environment")
    settings = Settings(_env_file=(str(base_env), str(local_env)))
    assert settings.GEMINI_MODEL == "from-environment"
