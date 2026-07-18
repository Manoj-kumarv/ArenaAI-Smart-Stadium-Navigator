"""JWT authentication utilities and RBAC dependency.

Handles password hashing, token generation, user retrieval,
and role-based access control (RBAC).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated, Callable

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.exceptions import AuthenticationError, AuthorizationError
from app.models import User, UserRole

logger = logging.getLogger(__name__)

# oauth2_scheme parses the authorization header for bearer tokens
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ─── Password hashing ─────────────────────────────────────────────────────────

def get_password_hash(password: str) -> str:
    """Generate a bcrypt password hash for a plain text password.

    Args:
        password: The plain text password to hash.

    Returns:
        The encoded string representation of the hash.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a hashed representation.

    Args:
        plain: The plain text password.
        hashed: The expected hash.

    Returns:
        True if the password is correct, False otherwise.
    """
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as exc:
        logger.error("Password verification error: %s", exc)
        return False


# ─── JWT ──────────────────────────────────────────────────────────────────────

def _create_token(data: dict, expires_delta: timedelta) -> str:
    """Helper to generate JWT tokens with an expiration date."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    """Generate a JWT access token for a user session.

    Args:
        user_id: Internal user identifier.
        role: User role name.

    Returns:
        The encoded JWT token.
    """
    return _create_token(
        {"sub": str(user_id), "role": role},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int) -> str:
    """Generate a long-lived JWT refresh token.

    Args:
        user_id: Internal user identifier.

    Returns:
        The encoded JWT token.
    """
    return _create_token(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


# ─── Current-user dependency ──────────────────────────────────────────────────

def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Retrieve the current logged-in user from the JWT bearer token.

    FastAPI dependency that extracts the session token, validates the JWT,
    and returns the User entity.

    Args:
        token: The parsed access token string.
        db: Database session.

    Returns:
        The matching User object.

    Raises:
        HTTPException: 401 Unauthorized if the token is invalid or user is missing.
    """
    credentials_exc = AuthenticationError(
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    ).to_http_exception()

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.get(User, int(user_id))
    if user is None or not user.is_active:
        raise credentials_exc
    return user


# ─── RBAC dependency factory ──────────────────────────────────────────────────

def require_role(*roles: UserRole) -> Callable[[User], User]:
    """FastAPI dependency factory enforcing role-based access control.

    Args:
        *roles: One or more allowed UserRoles.

    Returns:
        A dependency function that checks user authorization.
    """
    def _checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role not in roles:
            raise AuthorizationError(
                role=current_user.role.value,
                action="this action",
            ).to_http_exception()
        return current_user
    return _checker
