"""
PII filter and prompt-injection filter.
Both are called BEFORE the LLM and raise HTTPException(422) on violation.
"""
from __future__ import annotations

import re
from fastapi import HTTPException, status

# ─── PII patterns ─────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(
    r"(\+?1?\s?)?(\(?\d{3}\)?[\s.\-]?)(\d{3}[\s.\-]?\d{4})"
)

# ─── Prompt-injection patterns ────────────────────────────────────────────────
_INJECTION_PATTERNS: list[re.Pattern] = [
    re.compile(p, re.IGNORECASE)
    for p in [
        r"ignore\s+(all\s+)?previous\s+instructions?",
        r"system\s+prompt",
        r"act\s+as\s+(a\s+)?",
        r"jailbreak",
        r"dan\s+mode",
        r"you\s+are\s+now",
        r"forget\s+(all\s+)?previous",
        r"disregard\s+(all\s+)?previous",
        r"override\s+instructions?",
        r"pretend\s+(you\s+are|to\s+be)",
    ]
]


def check_prompt_injection(text: str) -> None:
    """Raise HTTP 422 if the input looks like a prompt-injection attempt."""
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Input rejected: potential prompt-injection pattern detected.",
            )


def check_pii_in_input(text: str) -> None:
    """Raise HTTP 422 if the input contains PII (email or phone)."""
    if _EMAIL_RE.search(text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Input rejected: email addresses are not permitted.",
        )
    if _PHONE_RE.search(text):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Input rejected: phone numbers are not permitted.",
        )


def scrub_pii_from_output(text: str) -> str:
    """Remove PII from any LLM output before returning to client."""
    text = _EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED-PHONE]", text)
    return text


def has_pii(text: str) -> bool:
    return bool(_EMAIL_RE.search(text) or _PHONE_RE.search(text))
