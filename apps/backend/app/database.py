"""Database connection and session management.

Configures SQLAlchemy engine and SessionLocal factory, and provides
the request dependency for retrieving clean database connections.
"""
from __future__ import annotations

from typing import Any, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

connect_args: dict[str, Any] = (
    {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
"""SQLAlchemy database engine."""

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""Database session factory."""


class Base(DeclarativeBase):
    """Base declarative class for all database models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session context.

    Ensures that session is closed after the request is finished.

    Yields:
        An active SQLAlchemy Session instance.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
