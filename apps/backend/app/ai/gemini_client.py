"""
Gemini API client with automatic fallback detection.
Returns None if Gemini is unavailable — callers switch to rule-based fallback.
"""
from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import; if missing, Gemini stays disabled
try:
    import google.generativeai as genai  # type: ignore
    _GENAI_AVAILABLE = True
except ImportError:
    _GENAI_AVAILABLE = False

_client_initialized = False


def _ensure_client() -> bool:
    global _client_initialized
    if not _GENAI_AVAILABLE or not settings.GEMINI_API_KEY.strip():
        return False
    if not _client_initialized:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _client_initialized = True
    return True


async def call_gemini(prompt: str, *, model: str = "gemini-1.5-flash") -> str | None:
    """
    Call Gemini and return the text response, or None on any failure.
    Timeout / API error → None (triggers rule-based fallback).
    """
    if not _ensure_client():
        return None
    try:
        import asyncio
        model_obj = genai.GenerativeModel(model)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: model_obj.generate_content(prompt)
        )
        return response.text
    except Exception as exc:
        logger.warning("Gemini call failed: %s — using fallback", exc)
        return None


async def call_gemini_json(prompt: str, **kwargs) -> dict[str, Any] | None:
    """Call Gemini and parse the JSON block from the response."""
    raw = await call_gemini(prompt, **kwargs)
    if raw is None:
        return None
    # Extract JSON from markdown code fence if present
    text = raw.strip()
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
        return None
