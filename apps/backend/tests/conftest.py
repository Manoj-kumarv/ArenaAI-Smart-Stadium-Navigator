"""Shared test fixtures — in-memory SQLite, FastAPI TestClient with overridden DB."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_access_token, get_password_hash
from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole

TEST_DATABASE_URL = "sqlite://"  # in-memory

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db):
    Base.metadata.create_all(bind=engine_test)
    app.dependency_overrides[get_db] = override_get_db

    # Seed demo users
    ops = User(
        username="ops_admin",
        email="ops@test.local",
        hashed_password=get_password_hash("OpsPass123!"),
        role=UserRole.ops_staff,
    )
    fan = User(
        username="fan_user",
        email="fan@test.local",
        hashed_password=get_password_hash("FanPass123!"),
        role=UserRole.fan,
    )
    db.add_all([ops, fan])
    db.commit()
    db.refresh(ops)
    db.refresh(fan)

    with TestClient(app, raise_server_exceptions=True) as c:
        c.ops_token = create_access_token(ops.id, ops.role.value)
        c.fan_token = create_access_token(fan.id, fan.role.value)
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


def ops_headers(client) -> dict:
    return {"Authorization": f"Bearer {client.ops_token}"}


def fan_headers(client) -> dict:
    return {"Authorization": f"Bearer {client.fan_token}"}
