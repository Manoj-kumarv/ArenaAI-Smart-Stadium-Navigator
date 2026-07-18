"""PII and prompt-injection filters.

Applies strict safety patterns on inputs prior to AI execution and scrubs
sensitive data from outputs before returning results.
"""
from __future__ import annotations

import re

from app.exceptions import InputValidationError

# ─── PII patterns ─────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(\+?1?\s?)?(\(?\d{3}\)?[\s.\-]?)(\d{3}[\s.\-]?\d{4})")
_SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

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
    """Scan query text and raise 422 Unprocessable Entity if malicious patterns are found.

    Args:
        text: Input string.

    Raises:
        InputValidationError: If input contains potential prompt-injection patterns.

    """
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            raise InputValidationError(
                detail="Input rejected: potential prompt-injection pattern detected."
            ).to_http_exception()


def check_pii_in_input(text: str) -> None:
    """Scan input text and raise 422 Unprocessable Entity if sensitive PII is found.

    Args:
        text: Input string.

    Raises:
        InputValidationError: If input contains emails, phone numbers, SSNs, or credit cards.

    """
    if _EMAIL_RE.search(text):
        raise InputValidationError(detail="Input rejected: email addresses are not permitted.").to_http_exception()
    if _PHONE_RE.search(text):
        raise InputValidationError(detail="Input rejected: phone numbers are not permitted.").to_http_exception()
    if _SSN_RE.search(text):
        raise InputValidationError(detail="Input rejected: SSN patterns are not permitted.").to_http_exception()
    if _CREDIT_CARD_RE.search(text):
        raise InputValidationError(detail="Input rejected: credit card numbers are not permitted.").to_http_exception()


def scrub_pii_from_output(text: str) -> str:
    """Mask sensitive personal information in AI model output strings.

    Args:
        text: The model response string.

    Returns:
        The sanitized string.

    """
    text = _EMAIL_RE.sub("[REDACTED-EMAIL]", text)
    text = _PHONE_RE.sub("[REDACTED-PHONE]", text)
    text = _SSN_RE.sub("[REDACTED-SSN]", text)
    text = _CREDIT_CARD_RE.sub("[REDACTED-CARD]", text)
    return text


def has_pii(text: str) -> bool:
    """Verify if any PII pattern is present in the text.

    Args:
        text: Target text string.

    Returns:
        True if any PII is detected, False otherwise.

    """
    return bool(
        _EMAIL_RE.search(text)
        or _PHONE_RE.search(text)
        or _SSN_RE.search(text)
        or _CREDIT_CARD_RE.search(text)
    )
