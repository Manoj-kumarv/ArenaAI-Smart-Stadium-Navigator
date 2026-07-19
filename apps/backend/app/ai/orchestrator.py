"""AI Orchestrator module.

Routes operational requests to the appropriate AI agent (Crowd, Fan, Incident)
or fallback templates, and handles atomic generation of trilingual announcements.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from app.ai.crowd_agent import run_crowd_agent
from app.ai.fallback import broadcast_fallback
from app.ai.fan_agent import run_fan_agent
from app.ai.gemini_client import call_gemini_json
from app.ai.incident_agent import run_incident_agent
from app.constants import AI_CACHE_TTL_SECONDS, BROADCAST_REQUIRED_LANGUAGES

logger = logging.getLogger(__name__)

# Simple in-memory TTL cache for agent responses
_cache: dict[str, tuple[float, Any]] = {}


def _cache_key(*args: Any) -> str:
    """Generate a cache key string from input arguments."""
    return "|".join(str(a) for a in args)


def _get_cached(key: str) -> Any | None:
    """Get value from cache if it has not expired."""
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < AI_CACHE_TTL_SECONDS:
        return entry[1]
    return None


def _set_cached(key: str, value: Any) -> None:
    """Set value in cache with current timestamp."""
    _cache[key] = (time.time(), value)


async def orchestrate_crowd(
    zone_id: str,
    zone_name: str,
    density_pct: float,
    capacity: int,
) -> dict[str, Any]:
    """Route density analysis query to Crowd Agent with caching.

    Args:
        zone_id: Zone unique identifier.
        zone_name: Readable name of the zone.
        density_pct: Current occupancy percentage.
        capacity: Zone capacity.

    Returns:
        Analysis dictionary (cause, recommendation, confidence).

    """
    key = _cache_key("crowd", zone_id, round(density_pct, 2))
    cached = _get_cached(key)
    if cached:
        logger.debug("Cache hit for crowd analysis of zone %s", zone_id)
        return cached

    result = await run_crowd_agent(zone_id, zone_name, density_pct, capacity)
    _set_cached(key, result)
    return result


async def orchestrate_fan(query: str) -> dict[str, Any]:
    """Route general fan Q&A query to Fan Assistant Agent.

    Args:
        query: User input query text.

    Returns:
        Trilingual answers dict.

    """
    logger.info("Orchestrating query to Fan Agent")
    return await run_fan_agent(query)


async def orchestrate_incident(
    title: str,
    description: str,
    zone_id: str | None,
) -> dict[str, Any]:
    """Route incident resolution task to Incident Agent.

    Args:
        title: Title of the incident.
        description: Detailed report of what happened.
        zone_id: ID of the zone where the incident occurred.

    Returns:
        Incident classification and playbook dict.

    """
    logger.info("Orchestrating incident resolution to Incident Agent")
    return await run_incident_agent(title, description, zone_id)


# Prompt template for trilingual broadcast announcements
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


async def generate_broadcast(
    incident_title: str,
    incident_description: str,
) -> dict[str, Any]:
    """Generate trilingual PA broadcast messages for an incident.

    Atomic: All three languages (EN, ES, AR) must succeed, or we discard
    partial output and return default fallback templates for all of them.

    Args:
        incident_title: The title of the incident.
        incident_description: The description of the incident.

    Returns:
        Dictionary containing keys 'message_en', 'message_es', 'message_ar',
        and a boolean flag 'used_ai'.

    """
    prompt = BROADCAST_PROMPT.format(
        title=incident_title,
        description=incident_description,
    )

    # First attempt
    result = await call_gemini_json(prompt)
    if not result or not BROADCAST_REQUIRED_LANGUAGES.issubset(result.keys()):
        # Retry once on failure/mismatch
        result = await call_gemini_json(prompt)

    # Atomicity check — all three must be present and contain non-empty text
    if (
        result
        and BROADCAST_REQUIRED_LANGUAGES.issubset(result.keys())
        and all(isinstance(result[k], str) and result[k].strip() for k in BROADCAST_REQUIRED_LANGUAGES)
    ):
        result["used_ai"] = True
        return result

    # Any failure → full fallback for all 3 languages
    logger.warning("Gemini failed broadcast generation, falling back to templates")
    return broadcast_fallback(incident_title, incident_description)
