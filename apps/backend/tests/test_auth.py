from __future__ import annotations

from tests.conftest import ops_headers


def test_signup_success(client):
    r = client.post(
        "/api/auth/signup",
        json={
            "username": "new_user",
            "email": "new_user@test.com",
            "password": "SecretPassword123!",
            "role": "fan",
        }
    )
    assert r.status_code == 201
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["role"] == "fan"


def test_signup_conflict(client):
    r = client.post(
        "/api/auth/signup",
        json={
            "username": "ops_admin",
            "email": "another@test.com",
            "password": "SecretPassword123!",
            "role": "ops_staff",
        }
    )
    assert r.status_code == 409
    assert "already registered" in r.json()["detail"].lower()


def test_login_success(client):
    r = client.post(
        "/api/auth/login",
        json={
            "username": "ops_admin",
            "password": "OpsPass123!",
        }
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["role"] == "ops_staff"


def test_login_invalid(client):
    r = client.post(
        "/api/auth/login",
        json={
            "username": "ops_admin",
            "password": "WrongPassword",
        }
    )
    assert r.status_code == 401
    assert "invalid credentials" in r.json()["detail"].lower()


def test_me_success(client):
    r = client.get("/api/auth/me", headers=ops_headers(client))
    assert r.status_code == 200
    body = r.json()
    assert body["username"] == "ops_admin"
    assert body["role"] == "ops_staff"
    assert "id" in body


def test_me_unauthorized(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401


def test_refresh_success(client):
    # First, login to get a refresh token
    login_res = client.post(
        "/api/auth/login",
        json={
            "username": "fan_user",
            "password": "FanPass123!",
        }
    )
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    # Now call /refresh
    r = client.post(
        "/api/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["role"] == "fan"


def test_refresh_invalid(client):
    r = client.post(
        "/api/auth/refresh",
        json={"refresh_token": "invalid-token-value"}
    )
    assert r.status_code == 401
    assert "invalid refresh token" in r.json()["detail"].lower()
