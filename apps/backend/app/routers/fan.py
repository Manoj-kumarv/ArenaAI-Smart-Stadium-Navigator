"""Fan router — public Q&A assistant (no auth required for fan queries)."""
from __future__ import annotations

from fastapi import APIRouter
from app.schemas import FanQueryRequest, FanQueryResponse
from app.ai.orchestrator import orchestrate_fan

router = APIRouter(prefix="/api/fan", tags=["fan"])


@router.post("/ask", response_model=FanQueryResponse)
async def ask_fan_assistant(payload: FanQueryRequest):
    """
    Public endpoint — any visitor can ask questions.
    Input validation (PII + injection filters) runs inside the agent.
    Returns answers in English, Spanish, and Arabic.
    """
    result = await orchestrate_fan(payload.query)
    return FanQueryResponse(**result)
