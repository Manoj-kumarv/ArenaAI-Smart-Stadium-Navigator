"""Gemini API client.

Handles calls to Google's Generative AI API with structured timeout,
exception safety, and automated fallback detection.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from app.config import settings
from app.constants import AI_REQUEST_TIMEOUT_SECONDS, GEMINI_MODEL_NAME

logger = logging.getLogger(__name__)

# Verify google.generativeai module availability
try:
    import google.generativeai as genai  # type: ignore[import]
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

_client_initialized = False


def _ensure_client() -> bool:
    """Initialize the Google Generative AI client if not already done.

    Returns:
        True if the client is ready for calls, False if API key is missing.

    """
    global _client_initialized
    if not _GENAI_AVAILABLE or not settings.GEMINI_API_KEY.strip():
        return False
    if not _client_initialized:
        try:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            _client_initialized = True
        except Exception as exc:
            logger.error("Failed to configure Google GenAI: %s", exc)
            return False
    return True


async def call_gemini(
    prompt: str,
    *,
    model: str = GEMINI_MODEL_NAME,
) -> str | None:
    """Call Google Gemini and return the raw text response.

    Executes the call inside an executor to prevent blocking the event loop.
    Implements a strict timeout; any network error, API exception, or timeout
    returns None, triggering rule-based fallbacks.

    Args:
        prompt: Prompt string sent to the model.
        model: Specific model name to execute.

    Returns:
        The response text or None if Gemini call fails or timeouts.

    """
    if not _ensure_client():
        return None

    try:
        model_obj = genai.GenerativeModel(model)
        loop = asyncio.get_event_loop()

        # Wrap generating function in a timeout block
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: model_obj.generate_content(prompt),
            ),
            timeout=float(AI_REQUEST_TIMEOUT_SECONDS),
        )
        return response.text
    except TimeoutError:
        logger.warning("Gemini call timed out after %ds", AI_REQUEST_TIMEOUT_SECONDS)
        return None
    except Exception as exc:
        logger.warning("Gemini call failed: %s — using fallback", exc)
        return None


async def call_gemini_json(
    prompt: str,
    **kwargs: Any,
) -> dict[str, Any] | None:
    """Call Google Gemini and extract the JSON block from response text.

    Args:
        prompt: The prompt text.
        **kwargs: Additional parameters passed to call_gemini.

    Returns:
        Parsed JSON dictionary or None if decoding/generation fails.

    """
    raw = await call_gemini(prompt, **kwargs)
    if raw is None:
        return None

    text = raw.strip()

    # Extract JSON block from markdown code fences (e.g. ```json ... ```)
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            try:
                return json.loads(part)
            except json.JSONDecodeError:
                continue
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.debug("Failed to decode JSON from Gemini output: %s", text[:100])
        return None
