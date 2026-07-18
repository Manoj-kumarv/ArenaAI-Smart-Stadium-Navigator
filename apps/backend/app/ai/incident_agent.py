"""Incident/Security Agent — classifies severity and produces a resolution playbook.
"""
from __future__ import annotations

from app.ai.fallback import incident_fallback
from app.ai.filters import check_pii_in_input, check_prompt_injection, scrub_pii_from_output
from app.ai.gemini_client import call_gemini_json

SCHEMA_KEYS = {"zone_id", "severity", "confidence", "cause", "recommendation"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}

PROMPT_TEMPLATE = """
You are an AI Incident/Security Agent for FIFA World Cup 2026 stadium operations.

Incident Report:
- Zone: {zone_id}
- Title: {title}
- Description: {description}

Task: Classify the incident severity and provide a step-by-step resolution playbook for operations staff.

Severity levels: low | medium | high | critical

Respond ONLY with valid JSON (no extra keys):
{{
  "zone_id": "{zone_id}",
  "severity": "<low|medium|high|critical>",
  "confidence": <float 0.0-1.0>,
  "cause": "<root-cause analysis, 1-2 sentences>",
  "recommendation": "<numbered step-by-step resolution playbook>"
}}
""".strip()


def _validate(data: dict | None, zone_id: str) -> bool:
    if not data:
        return False
    if not SCHEMA_KEYS.issubset(data.keys()):
        return False
    if data.get("severity") not in VALID_SEVERITIES:
        return False
    conf = data.get("confidence", -1)
    if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
        return False
    return True


def _severity_to_score(severity: str) -> float:
    return {"low": 0.25, "medium": 0.55, "high": 0.80, "critical": 0.95}.get(severity, 0.5)


async def run_incident_agent(
    title: str,
    description: str,
    zone_id: str | None,
) -> dict:
    check_prompt_injection(title)
    check_prompt_injection(description)
    check_pii_in_input(title + " " + description)

    prompt = PROMPT_TEMPLATE.format(
        zone_id=zone_id or "unknown",
        title=title,
        description=description,
    )

    result = await call_gemini_json(prompt)
    if not _validate(result, zone_id or "unknown"):
        result = await call_gemini_json(prompt)  # one retry

    if not _validate(result, zone_id or "unknown"):
        result = incident_fallback(title, description, zone_id)
    else:
        result["recommendation"] = scrub_pii_from_output(result["recommendation"])
        result["used_ai"] = True
        result["confidence"] = float(result["confidence"])
        # Ensure ai_severity_score derived from severity label
        result["ai_severity_score"] = _severity_to_score(result["severity"])

    return result
