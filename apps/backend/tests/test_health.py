from __future__ import annotations


def test_health_check_endpoint(client):
    """Verify that the health check endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["service"] == "arenaiq-backend"


def test_readiness_probe_endpoint(client):
    """Verify that the readiness probe endpoint returns 200 and checks db status."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert data["checks"]["database"] == "ok"
