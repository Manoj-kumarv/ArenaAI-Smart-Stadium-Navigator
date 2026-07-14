"""
AI Orchestrator — intent-based routing to the three agents.
Also handles the broadcast generation (EN + ES + AR atomicity).
"""
from __future__ import annotations

import functools
import time
import logging
from typing import Any

from app.ai.crowd_agent import run_crowd_agent
from app.ai.fan_agent import run_fan_agent
from app.ai.incident_agent import run_incident_agent
from app.ai.gemini_client import call_gemini_json
from app.ai.fallback import broadcast_fallback

logger = logging.getLogger(__name__)

# ─── Simple in-memory TTL cache (30s) ────────────────────────────────────────

_cache: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 30.0  # seconds


def _cache_key(*args) -> str:
    return "|".join(str(a) for a in args)


def _get_cached(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < _CACHE_TTL:
        return entry[1]
    return None


def _set_cached(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)


# ─── Orchestrator entry points ────────────────────────────────────────────────

async def orchestrate_crowd(
    zone_id: str,
    zone_name: str,
    density_pct: float,
    capacity: int,
) -> dict:
    """Route to Crowd Agent with caching."""
    key = _cache_key("crowd", zone_id, round(density_pct, 2))
    cached = _get_cached(key)
    if cached:
        logger.debug("Cache hit: crowd %s", zone_id)
        return cached
    result = await run_crowd_agent(zone_id, zone_name, density_pct, capacity)
    _set_cached(key, result)
    return result


async def orchestrate_fan(query: str) -> dict:
    """Route to Fan Assistant Agent."""
    return await run_fan_agent(query)


async def orchestrate_incident(
    title: str,
    description: str,
    zone_id: str | None,
) -> dict:
    """Route to Incident Agent."""
    return await run_incident_agent(title, description, zone_id)


# ─── Broadcast generator (atomic: all 3 langs or fail) ───────────────────────

BROADCAST_PROMPT = """
You are a PA announcer for the FIFA World Cup 2026.

Incident: {title}
Details: {description}

Generate a short, calm PA-style announcement (2-3 sentences) for each of the three languages below.
Do NOT include personal data, phone numbers, or email addresses.

Respond ONLY with valid JSON:
{{
  "message_en": "<English announcement>",
  "message_es": "<Spanish announcement>",
  "message_ar": "<Arabic announcement — right-to-left text>"
}}
""".strip()

BROADCAST_SCHEMA = {"message_en", "message_es", "message_ar"}


async def generate_broadcast(
    incident_title: str,
    incident_description: str,
) -> dict:
    """
    Property 7 (broadcast atomicity):
    All 3 languages must succeed or we return the fallback for ALL 3.
    Never a partial broadcast.
    """
    prompt = BROADCAST_PROMPT.format(
        title=incident_title,
        description=incident_description,
    )

    result = await call_gemini_json(prompt)
    # Retry once
    if not result or not BROADCAST_SCHEMA.issubset(result.keys()):
        result = await call_gemini_json(prompt)

    # Atomicity check — all three must be non-empty strings
    if (
        result
        and BROADCAST_SCHEMA.issubset(result.keys())
        and all(
            isinstance(result[k], str) and result[k].strip()
            for k in BROADCAST_SCHEMA
        )
    ):
        result["used_ai"] = True
        return result

    # Any failure → full fallback for all 3 languages
    return broadcast_fallback(incident_title, incident_description)
