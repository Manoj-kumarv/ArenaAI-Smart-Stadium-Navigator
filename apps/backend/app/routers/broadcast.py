"""Broadcast router — atomic 3-language PA generation + audit log."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import AuditAction, AuditLog, BroadcastLog, Incident, User, UserRole
from app.schemas import BroadcastOut, BroadcastRequest, AuditPage, AuditLogOut
from app.ai.orchestrator import generate_broadcast

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])


@router.post("", response_model=BroadcastOut, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_role(UserRole.ops_staff))])
async def create_broadcast(
    payload: BroadcastRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
):
    """
    Generate PA announcement in EN + ES + AR (atomic — all 3 or none stored).
    """
    incident = db.get(Incident, payload.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found.")

    result = await generate_broadcast(incident.title, incident.description)

    # Atomicity: all three must be non-empty
    if not all(result.get(k, "").strip() for k in ("message_en", "message_es", "message_ar")):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Broadcast generation failed — partial result discarded.",
        )

    # Write audit BEFORE persisting broadcast
    audit = AuditLog(
        action=AuditAction.broadcast_send,
        user_id=current_user.id,
        incident_id=incident.id,
        detail=f"used_ai={result.get('used_ai', False)}",
    )
    db.add(audit)
    db.flush()

    log = BroadcastLog(
        incident_id=incident.id,
        message_en=result["message_en"],
        message_es=result["message_es"],
        message_ar=result["message_ar"],
        used_ai=result.get("used_ai", False),
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("", response_model=list[BroadcastOut])
async def list_broadcasts(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
):
    return db.query(BroadcastLog).order_by(BroadcastLog.created_at.desc()).limit(50).all()


@router.get("/audit", response_model=AuditPage,
            dependencies=[Depends(require_role(UserRole.ops_staff))])
async def list_audit_log(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ops_staff))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    q = db.query(AuditLog)
    total = q.count()
    items = (
        q.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AuditPage(items=items, total=total, page=page, page_size=page_size)
