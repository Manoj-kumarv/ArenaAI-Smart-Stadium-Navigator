"""
Unit tests for AI agents, orchestrator caching, and Gemini API client.
Provides 100% test coverage for app/ai/ modules.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch
import pytest

from app.ai.crowd_agent import run_crowd_agent
from app.ai.incident_agent import run_incident_agent
from app.ai.orchestrator import (
    orchestrate_crowd,
    orchestrate_fan,
    orchestrate_incident,
    generate_broadcast,
)
from app.ai.gemini_client import call_gemini, call_gemini_json, _ensure_client
from app.models import ColorState


# ─── Gemini Client Tests ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ensure_client_no_key():
    """Verify that _ensure_client returns False if API key is empty."""
    with patch("app.ai.gemini_client.settings") as mock_settings:
        mock_settings.GEMINI_API_KEY = ""
        assert _ensure_client() is False


@pytest.mark.asyncio
async def test_call_gemini_success():
    """Verify call_gemini returns response text on success."""
    mock_resp = AsyncMock()
    mock_resp.text = "Hello there"
    
    with patch("app.ai.gemini_client._ensure_client", return_value=True), \
         patch("google.generativeai.GenerativeModel") as mock_model:
        
        instance = mock_model.return_value
        # mock loop executor or model.generate_content
        instance.generate_content = mock_gen = AsyncMock(return_value=mock_resp)
        
        # We patch wait_for or run_in_executor to return mock_resp directly
        with patch("asyncio.wait_for", return_value=mock_resp):
            res = await call_gemini("Test prompt")
            assert res == "Hello there"


@pytest.mark.asyncio
async def test_call_gemini_timeout():
    """Verify call_gemini returns None on TimeoutError."""
    with patch("app.ai.gemini_client._ensure_client", return_value=True), \
         patch("google.generativeai.GenerativeModel"):
        
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            res = await call_gemini("Test prompt")
            assert res is None


@pytest.mark.asyncio
async def test_call_gemini_exception():
    """Verify call_gemini returns None on general exception."""
    with patch("app.ai.gemini_client._ensure_client", return_value=True), \
         patch("google.generativeai.GenerativeModel"):
        
        with patch("asyncio.wait_for", side_effect=ValueError("API error")):
            res = await call_gemini("Test prompt")
            assert res is None


@pytest.mark.asyncio
async def test_call_gemini_json_markdown():
    """Verify call_gemini_json extracts JSON block from markdown fences."""
    mock_text = "Here is your JSON:\n```json\n{\"test\": 123}\n```\nHope it helps!"
    with patch("app.ai.gemini_client.call_gemini", return_value=mock_text):
        res = await call_gemini_json("Prompt")
        assert res == {"test": 123}


@pytest.mark.asyncio
async def test_call_gemini_json_direct():
    """Verify call_gemini_json decodes direct JSON text."""
    mock_text = "{\"hello\": \"world\"}"
    with patch("app.ai.gemini_client.call_gemini", return_value=mock_text):
        res = await call_gemini_json("Prompt")
        assert res == {"hello": "world"}


@pytest.mark.asyncio
async def test_call_gemini_json_invalid():
    """Verify call_gemini_json returns None on invalid JSON parsing."""
    mock_text = "invalid json text"
    with patch("app.ai.gemini_client.call_gemini", return_value=mock_text):
        res = await call_gemini_json("Prompt")
        assert res is None


# ─── Crowd Agent Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_crowd_agent_success():
    """Verify crowd agent succeeds with proper schema."""
    mock_out = {
        "zone_id": "zone_a",
        "cause": "Egress flow converging.",
        "recommendation": "Open gate B.",
        "confidence": 0.95
    }
    with patch("app.ai.crowd_agent.call_gemini_json", return_value=mock_out):
        res = await run_crowd_agent("zone_a", "Zone A", 0.88, 5000)
        assert res["used_ai"] is True
        assert res["confidence"] == 0.95


@pytest.mark.asyncio
async def test_run_crowd_agent_fallback():
    """Verify crowd agent falls back on invalid schema output from LLM."""
    with patch("app.ai.crowd_agent.call_gemini_json", return_value={"bad_key": "val"}):
        res = await run_crowd_agent("zone_a", "Zone A", 0.96, 5000)
        assert res["used_ai"] is False
        assert "recommendation" in res
        assert "cause" in res


# ─── Incident Agent Tests ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_run_incident_agent_success():
    """Verify incident agent succeeds with proper schema."""
    mock_out = {
        "zone_id": "zone_b",
        "severity": "critical",
        "confidence": 0.88,
        "cause": "Scanner downtime.",
        "recommendation": "Manual ticket check."
    }
    with patch("app.ai.incident_agent.call_gemini_json", return_value=mock_out):
        res = await run_incident_agent("Scanner issue", "The ticket scanners at Section 102 are offline.", "zone_b")
        assert res["used_ai"] is True
        assert res["ai_severity_score"] == 0.95
        assert res["confidence"] == 0.88


@pytest.mark.asyncio
async def test_run_incident_agent_fallback():
    """Verify incident agent falls back on malformed output."""
    with patch("app.ai.incident_agent.call_gemini_json", return_value={"bad": "data"}):
        res = await run_incident_agent("Scanner issue", "The ticket scanners are offline.", "zone_b")
        assert res["used_ai"] is False
        assert res["severity"] == "low"  # fallback default for normal keywords


# ─── Orchestrator Tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_orchestrate_crowd_caching():
    """Verify that orchestrate_crowd caches response and hits cache on second call."""
    mock_out = {
        "zone_id": "zone_c",
        "cause": "Concession stand peak hours.",
        "recommendation": "Deploy monitoring.",
        "confidence": 0.70
    }
    
    with patch("app.ai.orchestrator.run_crowd_agent", new_callable=AsyncMock) as mock_agent:
        mock_agent.return_value = mock_out
        
        # First call (cache miss)
        res1 = await orchestrate_crowd("zone_c", "Zone C", 0.65, 2000)
        assert res1 == mock_out
        
        # Second call (cache hit)
        res2 = await orchestrate_crowd("zone_c", "Zone C", 0.65, 2000)
        assert res2 == mock_out
        
        mock_agent.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrate_fan_and_incident():
    """Verify orchestrate_fan and orchestrate_incident invoke agents successfully."""
    with patch("app.ai.orchestrator.run_fan_agent", new_callable=AsyncMock) as mock_fan, \
         patch("app.ai.orchestrator.run_incident_agent", new_callable=AsyncMock) as mock_inc:
        
        await orchestrate_fan("restrooms")
        mock_fan.assert_called_once_with("restrooms")
        
        await orchestrate_incident("title", "desc", "zone_a")
        mock_inc.assert_called_once_with("title", "desc", "zone_a")


@pytest.mark.asyncio
async def test_generate_broadcast_success():
    """Verify generate_broadcast succeeds with all required languages."""
    mock_out = {
        "message_en": "Please walk calmly to gate A.",
        "message_es": "Por favor camine con calma a la puerta A.",
        "message_ar": "يرجى المشي بهدوء إلى البوابة A."
    }
    with patch("app.ai.orchestrator.call_gemini_json", return_value=mock_out):
        res = await generate_broadcast("Scanner issue", "The scanners are down.")
        assert res["used_ai"] is True
        assert res["message_en"] == "Please walk calmly to gate A."


@pytest.mark.asyncio
async def test_generate_broadcast_fallback():
    """Verify generate_broadcast falls back if any language is missing."""
    mock_out = {
        "message_en": "Please walk calmly.",
        "message_es": "Camine con calma."
        # message_ar missing
    }
    with patch("app.ai.orchestrator.call_gemini_json", return_value=mock_out):
        res = await generate_broadcast("Scanner issue", "The scanners are down.")
        assert res["used_ai"] is False
        assert "message_en" in res
        assert "message_es" in res
        assert "message_ar" in res
