"""
Named constants for the ArenaIQ backend.

Centralizes all magic numbers and strings used across the application,
improving maintainability and making business rules explicit.
"""
from __future__ import annotations

# ─── Zone Density Thresholds ──────────────────────────────────────────────────
# These thresholds determine zone color state based on occupancy percentage.
# Values are expressed as fractions (0.0 to 1.0).

DENSITY_THRESHOLD_YELLOW: float = 0.60
"""Density at or above this value transitions zone to 'yellow' (moderate)."""

DENSITY_THRESHOLD_RED: float = 0.85
"""Density at or above this value transitions zone to 'red' (high)."""

DENSITY_THRESHOLD_CRITICAL: float = 0.95
"""Density at or above this value transitions zone to 'critical' (severe)."""

DENSITY_MAXIMUM: float = 1.0
"""Maximum density value; any reading above this is capped."""

# ─── AI Agent Configuration ───────────────────────────────────────────────────

AI_CACHE_TTL_SECONDS: float = 30.0
"""Time-to-live for cached AI responses to reduce API costs."""

AI_MAX_RETRIES: int = 1
"""Number of retry attempts when Gemini returns invalid JSON schema."""

AI_REQUEST_TIMEOUT_SECONDS: int = 30
"""Maximum time to wait for a Gemini API response before falling back."""

GEMINI_MODEL_NAME: str = "gemini-flash-latest"
"""Default Gemini model used for AI agent responses."""

# ─── Rate Limiting ────────────────────────────────────────────────────────────

RATE_LIMIT_DEFAULT: str = "200/minute"
"""Default rate limit applied globally to all endpoints."""

RATE_LIMIT_AI_ENDPOINTS: str = "30/minute"
"""Rate limit for AI-intensive endpoints (crowd analysis, fan assistant)."""

RATE_LIMIT_RESOLVE: str = "20/minute"
"""Rate limit for incident resolution and broadcast generation."""

RATE_LIMIT_FAN_ASSISTANT: str = "15/minute"
"""Rate limit for public fan assistant queries."""

# ─── WebSocket & Telemetry ────────────────────────────────────────────────────

TELEMETRY_INTERVAL_MIN_SECONDS: float = 2.0
"""Minimum interval between telemetry simulation steps."""

TELEMETRY_INTERVAL_MAX_SECONDS: float = 3.0
"""Maximum interval between telemetry simulation steps."""

TELEMETRY_STARTUP_DELAY_SECONDS: float = 2.0
"""Delay before telemetry loop starts to let the app finish initialization."""

TELEMETRY_HISTORY_RETENTION_SECONDS: int = 180
"""Maximum age (3 minutes) for zone density history rows before cleanup."""

TELEMETRY_CLEANUP_INTERVAL_SECONDS: int = 30
"""How often the telemetry loop cleans up old history records."""

STALE_DATA_THRESHOLD_MS: int = 5000
"""Frontend: WebSocket data older than this triggers a stale-data warning."""

# ─── Simulation Parameters ────────────────────────────────────────────────────

SIMULATION_NOISE_STD_DEV: float = 0.04
"""Standard deviation of Gaussian noise applied to zone density each tick."""

SIMULATION_MEAN_REVERSION_RATE: float = 0.05
"""Rate at which zone density reverts toward its baseline value."""

SIMULATION_DENSITY_MAX_OVERSHOOT: float = 1.05
"""Maximum raw density value before capping (tests cap behavior)."""

# ─── KPI Calculations ─────────────────────────────────────────────────────────

KPI_WAIT_TIME_SCALE_FACTOR: float = 18.0
"""Scale factor converting average density to estimated wait time in minutes."""

# ─── Pagination Defaults ──────────────────────────────────────────────────────

DEFAULT_PAGE_SIZE: int = 20
"""Default number of items per page in paginated endpoints."""

MAX_PAGE_SIZE: int = 100
"""Maximum allowed page size to prevent excessive query load."""

BROADCAST_LOG_LIMIT: int = 50
"""Maximum number of broadcast logs returned in a single query."""

# ─── Security ─────────────────────────────────────────────────────────────────

MAX_REQUEST_BODY_BYTES: int = 1_048_576  # 1 MB
"""Maximum allowed request body size to prevent denial-of-service attacks."""

PII_DESCRIPTION_TRUNCATE_LENGTH: int = 120
"""Maximum characters from incident description used in broadcast fallback."""

# ─── Broadcast Schema ─────────────────────────────────────────────────────────

BROADCAST_REQUIRED_LANGUAGES: frozenset[str] = frozenset(
    {"message_en", "message_es", "message_ar"}
)
"""Required language keys for a valid broadcast response (atomicity check)."""
