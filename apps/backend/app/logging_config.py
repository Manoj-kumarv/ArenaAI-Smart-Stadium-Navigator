"""
Structured logging configuration for ArenaIQ.

Provides JSON-formatted log output with correlation IDs for
production observability, and human-readable output for development.

Features:
    - Structured JSON format with consistent field ordering
    - Automatic correlation ID injection from request context
    - Configurable log level via environment variables
    - Request metadata (path, method) in log entries
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

from app.middleware.correlation import get_correlation_id


class StructuredFormatter(logging.Formatter):
    """JSON log formatter for production observability.

    Produces machine-parseable log entries with consistent fields
    suitable for log aggregation pipelines (ELK, CloudWatch, etc.).

    Fields emitted:
        - timestamp: ISO 8601 timestamp
        - level: Log level name
        - message: Log message text
        - logger: Logger name
        - module: Source module
        - correlation_id: Request correlation ID (if available)
        - exception: Exception traceback (if present)
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON string.

        Args:
            record: The log record to format.

        Returns:
            A JSON-encoded string representing the log entry.
        """
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "correlation_id": get_correlation_id(),
        }

        # Include exception info if present
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if provided
        for key in ("user_id", "request_path", "request_method", "status_code"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


def setup_logging(
    level: str = "INFO",
    structured: bool = True,
) -> None:
    """Configure the root logger for the application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR).
        structured: If True, use JSON format; otherwise human-readable.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to prevent duplicate output
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    if structured:
        handler.setFormatter(StructuredFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
