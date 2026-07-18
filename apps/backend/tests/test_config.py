from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_config_log_level_validation():
    """Verify that only supported log levels are valid."""
    with pytest.raises(ValidationError):
        Settings(LOG_LEVEL="INVALID_LEVEL")


def test_config_secret_key_length():
    """Verify that a short secret key raises validation error."""
    with pytest.raises(ValidationError):
        Settings(SECRET_KEY="short")


def test_config_defaults():
    """Verify default configurations are set properly."""
    cfg = Settings()
    assert cfg.ACCESS_TOKEN_EXPIRE_MINUTES == 30
    assert cfg.ALGORITHM == "HS256"
    assert cfg.MAX_CONTENT_LENGTH == 1048576
