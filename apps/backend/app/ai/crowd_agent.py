"""Crowd Agent — explains zone congestion and recommends actions.
Returns strict JSON; retries once on schema mismatch; falls back to rule-based.
"""

from __future__ import annotations

from app.ai.fallback import crowd_fallback
from app.ai.gemini_client import call_gemini_json
from app.models import density_to_color

SCHEMA_KEYS = {"zone_id", "cause", "recommendation", "confidence"}

PROMPT_TEMPLATE = """
You are an AI crowd management agent for the FIFA World Cup 2026 stadium operations team.

Zone Information:
- Zone ID: {zone_id}
- Zone Name: {zone_name}
- Current Density: {density_pct:.0%}
- Status: {color_state}
- Capacity: {capacity} people

Task: Analyse the crowd situation and provide actionable guidance.

Respond ONLY with valid JSON matching this exact schema (no extra keys):
{{
  "zone_id": "{zone_id}",
  "cause": "<2-3 sentence explanation of likely congestion cause>",
  "recommendation": "<specific actionable steps for operations staff>",
  "confidence": <float 0.0-1.0>
}}
""".strip()


def _validate(data: dict | None, zone_id: str) -> bool:
    if not data:
        return False
    if not SCHEMA_KEYS.issubset(data.keys()):
        return False
    conf = data.get("confidence", -1)
    if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
        return False
    return True


async def run_crowd_agent(
    zone_id: str,
    zone_name: str,
    density_pct: float,
    capacity: int,
) -> dict:
    color_state = density_to_color(density_pct)
    prompt = PROMPT_TEMPLATE.format(
        zone_id=zone_id,
        zone_name=zone_name,
        density_pct=density_pct,
        color_state=color_state.value,
        capacity=capacity,
    )

    # First attempt
    result = await call_gemini_json(prompt)
    if not _validate(result, zone_id):
        # Retry once
        result = await call_gemini_json(prompt)

    if not _validate(result, zone_id):
        result = crowd_fallback(zone_id, zone_name, density_pct, color_state)
    else:
        result["used_ai"] = True
        result["confidence"] = float(result["confidence"])

    return result
