"""Authentication router.

Handles signup, login, token refresh, and user profile retrieval.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from app.config import settings
from app.database import get_db
from app.exceptions import AlreadyExistsError, AuthenticationError, AuthorizationError
from app.limiter import limiter
from app.models import User
from app.schemas import LoginRequest, RefreshRequest, SignupRequest, TokenResponse, UserMeResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/signup", response_model=TokenResponse, status_code=201)
@limiter.limit("20/minute")
async def signup(
    request: Request,
    payload: SignupRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Register a new user in the system.

    Rejects request if the username or email is already registered.

    Args:
        request: The incoming request (for rate limiting).
        payload: Signup payload (username, email, password, role).
        db: Database session.

    Returns:
        TokenResponse containing JWT access and refresh tokens.

    Raises:
        AlreadyExistsError: If the username or email is already registered.

    """
    if db.query(User).filter((User.username == payload.username) | (User.email == payload.email)).first():
        raise AlreadyExistsError("User", f"{payload.username}/{payload.email}").to_http_exception()

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("Successfully signed up user: %s (role: %s)", user.username, user.role.value)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        role=user.role.value,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("20/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Authenticate user credentials and return access + refresh tokens.

    Args:
        request: The incoming request (for rate limiting).
        payload: Login payload containing username and password.
        db: Database session.

    Returns:
        TokenResponse containing access and refresh tokens.

    Raises:
        AuthenticationError: If credentials are invalid.
        AuthorizationError: If the user account is disabled.

    """
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        # Log auth failure attempt (security requirement 6.5)
        logger.warning("Failed login attempt for username: %s", payload.username)
        raise AuthenticationError("Invalid credentials.").to_http_exception()

    if not user.is_active:
        logger.warning("Disabled account login attempt: %s", payload.username)
        raise AuthorizationError(user.role.value, "disabled account access").to_http_exception()

    logger.info("User successfully logged in: %s", user.username)
    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        role=user.role.value,
    )


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    payload: RefreshRequest,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """Issue a new access token using a valid refresh token.

    Args:
        request: The incoming request (for rate limiting).
        payload: RefreshRequest containing the refresh token.
        db: Database session.

    Returns:
        TokenResponse containing fresh access and refresh tokens.

    Raises:
        AuthenticationError: If the refresh token is invalid or user is not found.

    """
    try:
        data = jwt.decode(payload.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if data.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token.").to_http_exception()
        user_id = data.get("sub")
    except JWTError as exc:
        raise AuthenticationError(f"Invalid refresh token: {exc}").to_http_exception()

    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise AuthenticationError("User not found or disabled.").to_http_exception()

    return TokenResponse(
        access_token=create_access_token(user.id, user.role.value),
        refresh_token=create_refresh_token(user.id),
        role=user.role.value,
    )


@router.get("/me", response_model=UserMeResponse)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> dict[str, Any]:
    """Retrieve current authenticated user profiles.

    Args:
        current_user: The currently logged in User context.

    Returns:
        A dict containing user metadata (id, username, role).

    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.value,
    }
