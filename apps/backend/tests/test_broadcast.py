"""
Broadcast atomicity tests — Property 7.
If any one of the 3 languages fails, the entire broadcast is treated as failed
and nothing is stored.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import ops_headers
from app.models import Zone, ZoneType, Incident, BroadcastLog
from app.ai.orchestrator import generate_broadcast


def _seed(db):
    z = Zone(id="gate_a", name="Gate A", zone_type=ZoneType.gate, capacity=800, x=0, y=0, w=60, h=40)
    inc = Incident(
        zone_id="gate_a",
        title="Broadcast test incident",
        description="Long enough description for the broadcast test",
    )
    db.add_all([z, inc])
    db.commit()
    db.refresh(inc)
    return inc.id


# ─── Property 7: atomic broadcast ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_broadcast_all_three_languages_succeed():
    """All 3 populated → success, used_ai=True."""
    mock_response = {
        "message_en": "Attention guests: please move to the south concourse.",
        "message_es": "Atención: por favor diríjase al concurso sur.",
        "message_ar": "انتباه: يرجى التوجه إلى الممر الجنوبي.",
        "used_ai": True,
    }
    with patch("app.ai.orchestrator.call_gemini_json", new_callable=AsyncMock, return_value=mock_response):
        result = await generate_broadcast("Test", "Description")
    assert result["used_ai"] is True
    assert result["message_en"]
    assert result["message_es"]
    assert result["message_ar"]


@pytest.mark.asyncio
async def test_broadcast_falls_back_when_gemini_unavailable():
    """Gemini returns None → fallback templates used for all 3 languages."""
    with patch("app.ai.orchestrator.call_gemini_json", new_callable=AsyncMock, return_value=None):
        result = await generate_broadcast("Gate A overcrowding", "Large queue at Gate A")
    assert result["used_ai"] is False
    assert result["message_en"]
    assert result["message_es"]
    assert result["message_ar"]


@pytest.mark.asyncio
async def test_broadcast_partial_language_uses_fallback():
    """Missing one language key → fallback for ALL three (atomicity)."""
    partial = {"message_en": "Attention...", "message_es": ""}  # missing ar, es empty
    with patch("app.ai.orchestrator.call_gemini_json", new_callable=AsyncMock, return_value=partial):
        result = await generate_broadcast("Lost child", "Child missing in Section 120")
    # Must have all 3 (fallback kicks in)
    assert result["message_en"]
    assert result["message_es"]
    assert result["message_ar"]


def test_broadcast_api_stores_all_three(client, db):
    """End-to-end: successful broadcast via API stores all 3 language messages."""
    inc_id = _seed(db)

    mock_broadcast = {
        "message_en": "Attention: please move calmly.",
        "message_es": "Atención: muévase con calma.",
        "message_ar": "انتباه: يرجى التحرك بهدوء.",
        "used_ai": True,
    }

    with patch("app.routers.broadcast.generate_broadcast",
               new_callable=AsyncMock, return_value=mock_broadcast):
        r = client.post(
            "/api/broadcast",
            json={"incident_id": inc_id},
            headers=ops_headers(client),
        )

    assert r.status_code == 201
    body = r.json()
    assert body["message_en"]
    assert body["message_es"]
    assert body["message_ar"]

    # Verify persisted in DB
    from tests.conftest import TestingSessionLocal
    fresh_db = TestingSessionLocal()
    try:
        log = fresh_db.query(BroadcastLog).filter_by(incident_id=inc_id).first()
        assert log is not None
        assert log.message_en
        assert log.message_es
        assert log.message_ar
    finally:
        fresh_db.close()


def test_broadcast_fan_cannot_trigger(client, db):
    """Fan role cannot call broadcast endpoint."""
    from tests.conftest import fan_headers
    inc_id = _seed(db)
    r = client.post("/api/broadcast", json={"incident_id": inc_id},
                    headers=fan_headers(client))
    assert r.status_code == 403
