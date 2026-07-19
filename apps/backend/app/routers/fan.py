"""Fan assistant router.

Provides public Q&A assistant endpoints for stadium visitors.
Ensures inputs are sanitized and checked for PII and prompt injection.
"""

import logging
from typing import Any

from fastapi import APIRouter, Request

from app.ai.filters import check_pii_in_input, check_prompt_injection
from app.ai.orchestrator import orchestrate_fan
from app.limiter import limiter
from app.schemas import FanQueryRequest, FanQueryResponse

router = APIRouter(prefix="/api/fan", tags=["fan"])
logger = logging.getLogger(__name__)


@router.post("/ask", response_model=FanQueryResponse)
@limiter.limit("15/minute")
async def ask_fan_assistant(
    request: Request,
    payload: FanQueryRequest,
) -> dict[str, Any]:
    """Public Q&A assistant endpoint.

    Accepts questions from fans and returns answers in EN, ES, and AR.
    Enforces rate limits and checks input for security/privacy violations
    (prompt injection and PII) prior to AI execution.

    Args:
        request: The incoming FastAPI request (used by rate limiter).
        payload: The request body containing the query text.

    Returns:
        A dict containing trilingual answers, confidence score, and used_ai flag.

    """
    # Security filters on query
    check_prompt_injection(payload.query)
    check_pii_in_input(payload.query)

    logger.info("Routing query to Fan Agent: %s", payload.query[:50])
    result = await orchestrate_fan(payload.query)
    return result
