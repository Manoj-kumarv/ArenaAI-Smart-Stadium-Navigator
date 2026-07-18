"""Rate limiting configuration for the ArenaIQ API.

Enforces limits on incoming requests using slowapi to mitigate abuse and
prevent Denial of Service (DoS) conditions.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.constants import RATE_LIMIT_DEFAULT

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[RATE_LIMIT_DEFAULT],
)
"""Global shared rate limiter instance."""
