"""Custom exception hierarchy for the ArenaIQ application.

Maps domain-specific errors to appropriate HTTP status codes, providing
structured error handling across all routers and services.

Exception Hierarchy:
    ArenaIQError (base)
    ├── NotFoundError          → 404
    ├── AlreadyExistsError     → 409
    ├── AlreadyResolvedError   → 400
    ├── ValidationError        → 422
    ├── AuthenticationError    → 401
    ├── AuthorizationError     → 403
    ├── AIServiceError         → 502
    └── RateLimitError         → 429
"""

from __future__ import annotations

from fastapi import HTTPException, status


class ArenaIQError(Exception):
    """Base exception for all ArenaIQ domain errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)

    def to_http_exception(self) -> HTTPException:
        """Convert to a FastAPI HTTPException for consistent error responses."""
        return HTTPException(status_code=self.status_code, detail=self.detail)


class NotFoundError(ArenaIQError):
    """Raised when a requested resource does not exist."""

    status_code = status.HTTP_404_NOT_FOUND

    def __init__(self, resource: str, identifier: str | int) -> None:
        super().__init__(f"{resource} '{identifier}' not found.")


class AlreadyExistsError(ArenaIQError):
    """Raised when attempting to create a resource that already exists."""

    status_code = status.HTTP_409_CONFLICT

    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} '{identifier}' is already registered.")


class AlreadyResolvedError(ArenaIQError):
    """Raised when attempting to resolve an incident that is already resolved."""

    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, incident_id: int) -> None:
        super().__init__(f"Incident {incident_id} is already resolved.")


class InputValidationError(ArenaIQError):
    """Raised when user input fails validation (PII, injection, format)."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class AuthenticationError(ArenaIQError):
    """Raised when authentication credentials are invalid or missing."""

    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Could not validate credentials."

    def __init__(self, detail: str | None = None, headers: dict[str, str] | None = None) -> None:
        self.headers = headers
        super().__init__(detail)

    def to_http_exception(self) -> HTTPException:
        """Convert to a FastAPI HTTPException with headers support."""
        return HTTPException(status_code=self.status_code, detail=self.detail, headers=self.headers)


class AuthorizationError(ArenaIQError):
    """Raised when the authenticated user lacks required permissions."""

    status_code = status.HTTP_403_FORBIDDEN

    def __init__(self, role: str, action: str = "this action") -> None:
        super().__init__(f"Role '{role}' is not permitted for {action}.")


class AIServiceError(ArenaIQError):
    """Raised when the AI service fails and fallback cannot recover."""

    status_code = status.HTTP_502_BAD_GATEWAY
    detail = "AI service is temporarily unavailable."


class BroadcastAtomicityError(ArenaIQError):
    """Raised when broadcast generation fails atomicity check (partial languages)."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = "Broadcast generation failed — partial result discarded."


class ResolutionRollbackError(ArenaIQError):
    """Raised when incident resolution fails and the transaction is rolled back."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, incident_id: int, reason: str) -> None:
        super().__init__(f"Resolution of incident {incident_id} failed and was rolled back: {reason}")
