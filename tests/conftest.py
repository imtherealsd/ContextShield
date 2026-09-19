"""Pytest configuration and fixtures for ContextShield."""

import asyncio

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.audit import audit_service


@pytest.fixture(autouse=True)
def clean_audit_records():
    """Clears audit records before and after each test."""
    asyncio.run(audit_service.clear())
    yield
    asyncio.run(audit_service.clear())


@pytest.fixture
def client():
    """TestClient for synchronous HTTP requests."""
    with TestClient(app) as test_client:
        yield test_client
