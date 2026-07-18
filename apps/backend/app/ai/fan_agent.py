"""Fan Assistant Agent — answers fan queries in English, Spanish, and Arabic.
Supports RTL (Arabic) responses.
"""
from __future__ import annotations

from app.ai.fallback import fan_fallback
from app.ai.filters import check_pii_in_input, check_prompt_injection, scrub_pii_from_output
from app.ai.gemini_client import call_gemini_json

SCHEMA_KEYS = {"answer_en", "answer_es", "answer_ar", "confidence"}

PROMPT_TEMPLATE = """
You are ArenaIQ Fan Assistant for the FIFA World Cup 2026.
A fan has asked: "{query}"

Stadium context:
- Venue: World Cup 2026 Stadium
- Gates: A (north-west), B (north-east), C (south-west), D (south-east)
- Concourses: North (upper) and South (lower)
- Medical stations: near Section 101 (North) and Section 110 (South)
- Accessibility: step-free access at Gates A and B, Sections 102, 104, 111, 113, 121, 123
- Food: kiosks at North and South Concourses; halal and vegetarian options available
- Volunteer posts: 5 throughout stadium, volunteers wear orange vests

Strict Domain Boundary Rule:
- If the fan's query is completely unrelated to the stadium, navigation, directions, food, medical stations, facilities, or the World Cup (e.g., general mathematics, writing computer code, general knowledge, unrelated puzzles, etc.), do NOT answer it.
- Instead, politely refuse to answer in all three languages, explaining that you are a dedicated ArenaIQ stadium assistant and can only help with stadium-related questions.

Respond in THREE languages. Use natural, helpful, stadium PA style.

Respond ONLY with valid JSON (no extra keys):
{{
  "answer_en": "<English answer, 1-3 sentences>",
  "answer_es": "<Spanish answer, 1-3 sentences>",
  "answer_ar": "<Arabic answer, 1-3 sentences, right-to-left text>",
  "confidence": <float 0.0-1.0>
}}
""".strip()


def _validate(data: dict | None) -> bool:
    if not data:
        return False
    if not SCHEMA_KEYS.issubset(data.keys()):
        return False
    conf = data.get("confidence", -1)
    if not isinstance(conf, (int, float)) or not (0.0 <= float(conf) <= 1.0):
        return False
    return True


async def run_fan_agent(query: str) -> dict:
    # Security filters run before LLM
    check_prompt_injection(query)
    check_pii_in_input(query)

    prompt = PROMPT_TEMPLATE.format(query=query)

    result = await call_gemini_json(prompt)
    if not _validate(result):
        result = await call_gemini_json(prompt)  # one retry

    if not _validate(result):
        result = fan_fallback(query)
    else:
        # Scrub any PII from LLM output
        for key in ("answer_en", "answer_es", "answer_ar"):
            result[key] = scrub_pii_from_output(result[key])
        result["used_ai"] = True
        result["confidence"] = float(result["confidence"])

    return result
