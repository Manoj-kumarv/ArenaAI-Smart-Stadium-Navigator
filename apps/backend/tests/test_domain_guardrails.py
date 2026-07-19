"""Tests for Strict Domain Boundary Rules and Guardrails.
Verifies that the fan assistant prompt contains strict rules rejecting out-of-domain topics
(math, coding, general knowledge) and validates the agent behavior.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.ai.fan_agent import PROMPT_TEMPLATE, run_fan_agent


def test_prompt_template_has_strict_domain_rules():
    """Assert that the PROMPT_TEMPLATE contains the domain boundary security requirements."""
    assert "Strict Domain Boundary Rule" in PROMPT_TEMPLATE
    assert "unrelated to the stadium" in PROMPT_TEMPLATE
    assert "mathematics" in PROMPT_TEMPLATE
    assert "computer code" in PROMPT_TEMPLATE
    assert "politely refuse" in PROMPT_TEMPLATE


@pytest.mark.asyncio
async def test_fan_agent_handles_domain_refusal_response():
    """Verify that the agent correctly returns the refuse messages when LLM generates refusal."""
    mock_refusal = {
        "answer_en": "As your ArenaIQ Stadium Assistant, I can only help you with questions related to the World Cup 2026 Stadium.",
        "answer_es": "Como su asistente de estadio ArenaIQ, solo puedo ayudarle con preguntas relacionadas con el Estadio.",
        "answer_ar": "بصفتي مساعد ملعب ArenaIQ، لا يمكنني مساعدتك إلا في الأسئلة المتعلقة بالملعب.",
        "confidence": 1.0,
    }

    with patch("app.ai.fan_agent.call_gemini_json", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_refusal

        result = await run_fan_agent("What is 2+9*23-5687")

        assert result["used_ai"] is True
        assert "stadium-related questions" in result["answer_en"] or "Stadium" in result["answer_en"]
        assert result["confidence"] == 1.0
        mock_call.assert_called_once()


@pytest.mark.asyncio
async def test_fan_agent_fallback_on_invalid_response():
    """Verify that the agent falls back safely if the LLM output doesn't match expected structure."""
    with patch("app.ai.fan_agent.call_gemini_json", new_callable=AsyncMock) as mock_call:
        # Return invalid dictionary schema
        mock_call.return_value = {"bad_key": "some text"}

        result = await run_fan_agent("Where is gate A?")

        assert result["used_ai"] is False
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0
