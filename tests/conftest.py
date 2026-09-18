"""Pytest configuration and fixtures for ContextShield."""

from dotenv import load_dotenv
load_dotenv(".env")
load_dotenv(".env.local", override=True)

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.audit import audit_service


@pytest.fixture(autouse=True)
def clean_audit_records():
    """Clears in-memory audit logs before and after each test."""
    audit_service.clear()
    yield
    audit_service.clear()


@pytest.fixture
def client():
    """TestClient for synchronous HTTP requests."""
    with TestClient(app) as test_client:
        yield test_client
