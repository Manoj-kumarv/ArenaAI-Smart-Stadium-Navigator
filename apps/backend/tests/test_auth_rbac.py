"""
RBAC tests — Property 3.
Every write endpoint must return 403 when called with a fan role token.
"""
from __future__ import annotations

import pytest
from tests.conftest import ops_headers, fan_headers
from app.models import Zone, ZoneType


def seed_zone(db):
    z = Zone(id="gate_a", name="Gate A", zone_type=ZoneType.gate,
              capacity=800, x=200, y=10, w=80, h=50)
    db.add(z)
    db.commit()
    return z


def seed_incident(client, db):
    seed_zone(db)
    r = client.post(
        "/api/incidents",
        json={"zone_id": "gate_a", "title": "Test incident for RBAC", "description": "Description long enough"},
        headers=ops_headers(client),
    )
    assert r.status_code == 201
    return r.json()["id"]


# ─── Write endpoints that must reject fan role ────────────────────────────────

def test_create_incident_fan_gets_403(client, db):
    seed_zone(db)
    r = client.post(
        "/api/incidents",
        json={"title": "Fan trying to create", "description": "Should be rejected by RBAC"},
        headers=fan_headers(client),
    )
    assert r.status_code == 403


def test_resolve_incident_fan_gets_403(client, db):
    inc_id = seed_incident(client, db)
    r = client.post(f"/api/incidents/{inc_id}/resolve", headers=fan_headers(client))
    assert r.status_code == 403


def test_delete_incident_fan_gets_403(client, db):
    inc_id = seed_incident(client, db)
    r = client.delete(f"/api/incidents/{inc_id}", headers=fan_headers(client))
    assert r.status_code == 403


def test_zone_action_fan_gets_403(client, db):
    seed_zone(db)
    r = client.post(
        "/api/zones/action",
        json={"zone_id": "gate_a", "action": "broadcast", "detail": "test"},
        headers=fan_headers(client),
    )
    assert r.status_code == 403


def test_broadcast_create_fan_gets_403(client, db):
    inc_id = seed_incident(client, db)
    r = client.post(
        "/api/broadcast",
        json={"incident_id": inc_id},
        headers=fan_headers(client),
    )
    assert r.status_code == 403


def test_audit_log_fan_gets_403(client, db):
    r = client.get("/api/broadcast/audit", headers=fan_headers(client))
    assert r.status_code == 403


# ─── Ops endpoints that SHOULD work ──────────────────────────────────────────

def test_create_incident_ops_succeeds(client, db):
    seed_zone(db)
    r = client.post(
        "/api/incidents",
        json={"zone_id": "gate_a", "title": "Valid ops incident", "description": "Long enough description here"},
        headers=ops_headers(client),
    )
    assert r.status_code == 201


def test_unauthenticated_write_gets_401(client, db):
    r = client.post(
        "/api/incidents",
        json={"title": "No token", "description": "Missing auth token"},
    )
    assert r.status_code == 401
