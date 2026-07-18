"""Broadcast router.

Generates trilingual PA announcements for stadium security incidents.
Ensures atomicity (all or nothing) across the three languages.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.ai.orchestrator import generate_broadcast
from app.auth import get_current_user, require_role
from app.database import get_db
from app.exceptions import BroadcastAtomicityError, NotFoundError
from app.limiter import limiter
from app.models import AuditAction, AuditLog, BroadcastLog, Incident, User, UserRole
from app.schemas import AuditPage, BroadcastOut, BroadcastRequest

router = APIRouter(prefix="/api/broadcast", tags=["broadcast"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=BroadcastOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(UserRole.ops_staff))],
)
@limiter.limit("20/minute")
async def create_broadcast(
    request: Request,
    payload: BroadcastRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_role(UserRole.ops_staff))],
) -> BroadcastLog:
    """Generate a PA announcement in English, Spanish, and Arabic for an incident.

    Atomic: all three languages must succeed, or the request fails and nothing is stored.
    Logs action to the audit log.

    Args:
        request: The incoming request (used by rate limiter).
        payload: The incident details for broadcast generation.
        db: Database session.
        current_user: The authenticated staff member.

    Returns:
        The generated trilingual broadcast log.

    Raises:
        NotFoundError: If the incident does not exist.
        BroadcastAtomicityError: If any of the languages fail to generate.

    """
    incident = db.get(Incident, payload.incident_id)
    if not incident:
        raise NotFoundError("Incident", payload.incident_id).to_http_exception()

    result = await generate_broadcast(incident.title, incident.description)

    # Atomicity: all three must be non-empty
    if not all(result.get(k, "").strip() for k in ("message_en", "message_es", "message_ar")):
        raise BroadcastAtomicityError().to_http_exception()

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

    logger.info(
        "Broadcast generated successfully for incident %d. AI used: %s",
        incident.id,
        result.get("used_ai", False),
    )
    return log


@router.get("", response_model=list[BroadcastOut])
async def list_broadcasts(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[BroadcastLog]:
    """Retrieve the list of recent generated PA broadcasts.

    Returns up to 50 logs, ordered by creation date (newest first).

    Args:
        db: Database session.
        _: Authenticated user context.

    Returns:
        A list of BroadcastLog entities.

    """
    return db.query(BroadcastLog).order_by(BroadcastLog.created_at.desc()).limit(50).all()


@router.get(
    "/audit",
    response_model=AuditPage,
    dependencies=[Depends(require_role(UserRole.ops_staff))],
)
async def list_audit_log(
    db: Annotated[Session, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.ops_staff))],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> AuditPage:
    """List historical security audit logs.

    Only permitted for ops_staff. Ordered by creation date (newest first).

    Args:
        db: Database session.
        _: Authenticated staff member context.
        page: Page number for pagination.
        page_size: Number of records per page.

    Returns:
        An AuditPage object with list items and pagination metadata.

    """
    q = db.query(AuditLog)
    total = q.count()
    items = (
        q.order_by(AuditLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return AuditPage(items=items, total=total, page=page, page_size=page_size)
