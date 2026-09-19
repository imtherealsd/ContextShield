"""Pytest configuration and fixtures for ContextShield."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.audit import audit_service


@pytest_asyncio.fixture(autouse=True)
async def clean_audit_records():
    """Clears audit records before and after each test."""
    await audit_service.clear()
    yield
    await audit_service.clear()


@pytest.fixture
def client():
    """TestClient for synchronous HTTP requests."""
    with TestClient(app) as test_client:
        yield test_client
