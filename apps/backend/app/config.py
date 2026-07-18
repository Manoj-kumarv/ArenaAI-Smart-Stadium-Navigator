"""
Configuration settings for the ArenaIQ backend.

Uses pydantic-settings to load configuration from environment variables
or .env files with automatic validation.
"""
from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings class validating environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Key used for JWT token signing. Change in production.",
    )
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API Key for running operations agents.",
    )
    DATABASE_URL: str = Field(
        default="sqlite:///./arenaiq.db",
        description="Database connection URL.",
    )
    FRONTEND_ORIGIN: str = Field(
        default="http://localhost:5173",
        description="Main allowed origin for CORS requests.",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT Access Token expiration duration in minutes.",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="JWT Refresh Token expiration duration in days.",
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Cryptographic algorithm used for JWT token signing.",
    )

    # Observability
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Default logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    ENABLE_STRUCTURED_LOGGING: bool = Field(
        default=True,
        description="If true, logs are output in JSON format.",
    )

    # Security
    MAX_CONTENT_LENGTH: int = Field(
        default=1048576,  # 1 MB
        description="Maximum request body size in bytes to prevent DoS.",
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate that the log level is supported."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {allowed}")
        return upper_v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key strength in production/development."""
        if len(v) < 16:
            raise ValueError("SECRET_KEY must be at least 16 characters long.")
        return v


settings = Settings()
