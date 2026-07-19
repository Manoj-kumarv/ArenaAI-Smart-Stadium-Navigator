"""Property tests for zone color thresholds and density cap.

Property 1 — color thresholds (parametrized boundary values)
Property 2 — density_pct > 1.0 is capped to 1.0
"""

from __future__ import annotations

import pytest
from hypothesis import given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from app.models import ColorState, cap_density, density_to_color

# ─── Property 1: exact boundary checks ───────────────────────────────────────


@pytest.mark.parametrize(
    "density,expected",
    [
        (0.0, ColorState.green),
        (0.59, ColorState.green),
        (0.599, ColorState.green),
        (0.60, ColorState.yellow),  # boundary: 0.60 → yellow
        (0.60001, ColorState.yellow),
        (0.84, ColorState.yellow),
        (0.849, ColorState.yellow),
        (0.85, ColorState.red),  # boundary: 0.85 → red
        (0.851, ColorState.red),
        (0.94, ColorState.red),
        (0.949, ColorState.red),
        (0.95, ColorState.critical),  # boundary: 0.95 → critical
        (0.951, ColorState.critical),
        (1.0, ColorState.critical),
    ],
)
def test_zone_color_thresholds(density: float, expected: ColorState):
    assert density_to_color(density) == expected


# ─── Property 2: density cap ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected_val,expected_flag",
    [
        (0.5, 0.5, False),
        (1.0, 1.0, False),
        (1.001, 1.0, True),
        (1.5, 1.0, True),
        (2.0, 1.0, True),
        (0.0, 0.0, False),
    ],
)
def test_density_cap(raw: float, expected_val: float, expected_flag: bool):
    val, flag = cap_density(raw)
    assert val == expected_val
    assert flag == expected_flag


# ─── Hypothesis: color is always a valid ColorState ──────────────────────────


@given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
@h_settings(max_examples=500)
def test_color_always_valid(density: float):
    result = density_to_color(density)
    assert result in ColorState.__members__.values()


# ─── Hypothesis: cap always returns [0, 1] ───────────────────────────────────


@given(st.floats(min_value=0.0, max_value=10.0, allow_nan=False))
@h_settings(max_examples=300)
def test_cap_always_in_range(raw: float):
    val, _ = cap_density(raw)
    assert 0.0 <= val <= 1.0


# ─── Zones API Integration Tests ──────────────────────────────────────────────

from unittest.mock import AsyncMock, patch

from app.models import Zone, ZoneType
from tests.conftest import ops_headers


def _seed_zone(db) -> Zone:
    z = Zone(id="gate_a", name="Gate A", zone_type=ZoneType.gate, capacity=800, x=0, y=0, w=60, h=40)
    db.add(z)
    db.commit()
    db.refresh(z)
    return z


def test_list_zones_success(client, db):
    _seed_zone(db)
    r = client.get("/api/zones", headers=ops_headers(client))
    assert r.status_code == 200
    body = r.json()
    assert len(body) >= 1
    assert body[0]["id"] == "gate_a"


def test_get_zone_not_found(client):
    r = client.get("/api/zones/unknown_zone", headers=ops_headers(client))
    assert r.status_code == 404


def test_analyse_zone_success(client, db):
    _seed_zone(db)
    mock_analysis = {
        "zone_id": "gate_a",
        "cause": "Egress flow converging.",
        "recommendation": "Deploy barrier.",
        "confidence": 0.88,
        "used_ai": True,
    }
    with patch("app.routers.zones.orchestrate_crowd", new_callable=AsyncMock, return_value=mock_analysis):
        r = client.post("/api/zones/gate_a/analyse", headers=ops_headers(client))
    assert r.status_code == 200
    body = r.json()
    assert body["zone_id"] == "gate_a"
    assert body["used_ai"] is True


def test_zone_action_success(client, db):
    _seed_zone(db)
    r = client.post(
        "/api/zones/action",
        json={"zone_id": "gate_a", "action": "deploy_volunteers", "detail": "send two volunteers"},
        headers=ops_headers(client),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["action"] == "deploy_volunteers"
    assert "audit_id" in body


def test_kpi_summary_success(client, db):
    _seed_zone(db)
    r = client.get("/api/zones/kpi/summary")
    assert r.status_code == 200
    body = r.json()
    assert "attendance" in body
    assert "active_incidents" in body
    assert "avg_wait_minutes" in body
