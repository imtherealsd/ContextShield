"""Tests for GET /v1/shield/health."""

from fastapi.testclient import TestClient


def test_health_endpoint_success(client: TestClient):
    """GET /v1/shield/health should return ok and explicit Moss status."""
    response = client.get("/v1/shield/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "moss" in data
    if data["moss"]["status"] == "ready":
        assert data["moss"]["loaded"] is True
        assert data["moss"]["index_name"] == "contextshield-security"
    else:
        assert data["moss"]["status"] in ("not_configured", "error")
        assert data["moss"]["loaded"] is False

