"""Incident resolution and rollback tests — Property 8.
Simulates a mid-resolution failure and asserts:
  - incident status reverts to 'open'
  - no partial audit rows persist
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from app.models import AuditLog, Incident, IncidentStatus, Zone, ZoneType
from tests.conftest import ops_headers


def _seed(db):
    z = Zone(id="gate_a", name="Gate A", zone_type=ZoneType.gate, capacity=800, x=0, y=0, w=60, h=40)
    inc = Incident(
        zone_id="gate_a",
        title="Test rollback incident",
        description="Description long enough to pass validation",
        status=IncidentStatus.open,
    )
    db.add_all([z, inc])
    db.commit()
    db.refresh(inc)
    return inc.id


# ─── Property 8: rollback on AI failure ──────────────────────────────────────


def test_incident_rollback_on_ai_failure(client, db):
    """When the AI agent raises an exception mid-workflow, the incident status
    must revert to 'open' and no partial audit rows should persist.
    """
    inc_id = _seed(db)

    # Confirm initial state
    inc = db.get(Incident, inc_id)
    assert inc.status == IncidentStatus.open

    initial_audit_count = db.query(AuditLog).count()

    # Patch orchestrate_incident to raise an exception
    with patch(
        "app.routers.incidents.orchestrate_incident",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Simulated AI failure"),
    ):
        r = client.post(f"/api/incidents/{inc_id}/resolve", headers=ops_headers(client))

    assert r.status_code == 500
    assert "rolled back" in r.json()["detail"].lower()

    # Re-fetch from a fresh DB session
    from tests.conftest import TestingSessionLocal

    fresh_db = TestingSessionLocal()
    try:
        reverted = fresh_db.get(Incident, inc_id)
        assert reverted is not None
        assert reverted.status == IncidentStatus.open, f"Expected 'open' after rollback, got '{reverted.status}'"
        # No partial audit rows should remain
        final_audit_count = fresh_db.query(AuditLog).count()
        assert final_audit_count == initial_audit_count, (
            f"Partial audit rows leaked: before={initial_audit_count}, after={final_audit_count}"
        )
    finally:
        fresh_db.close()


def test_incident_resolve_success(client, db):
    """Happy-path: successful resolution updates status and writes one audit row."""
    inc_id = _seed(db)

    mock_result = {
        "zone_id": "gate_a",
        "severity": "high",
        "confidence": 0.82,
        "cause": "Overcrowding detected",
        "recommendation": "Deploy volunteers",
        "used_ai": False,
        "ai_severity_score": 0.82,
    }

    with patch(
        "app.routers.incidents.orchestrate_incident",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        r = client.post(f"/api/incidents/{inc_id}/resolve", headers=ops_headers(client))

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "resolved"
    assert body["incident_id"] == inc_id
    assert "audit_id" in body


def test_incident_already_resolved_returns_400(client, db):
    inc_id = _seed(db)

    mock_result = {
        "zone_id": "gate_a",
        "severity": "low",
        "confidence": 0.5,
        "cause": "Minor",
        "recommendation": "Monitor",
        "used_ai": False,
        "ai_severity_score": 0.5,
    }

    with patch("app.routers.incidents.orchestrate_incident", new_callable=AsyncMock, return_value=mock_result):
        client.post(f"/api/incidents/{inc_id}/resolve", headers=ops_headers(client))
        r2 = client.post(f"/api/incidents/{inc_id}/resolve", headers=ops_headers(client))

    assert r2.status_code == 400
