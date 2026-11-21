"""Integration tests: password-reset flow (forgot → email → reset → session killed)."""

import itertools
from unittest.mock import AsyncMock, patch

import pytest

_counter = itertools.count(1000)  # offset from test_auth.py counter


def _unique_user(prefix: str = "pwreset") -> dict:
    n = next(_counter)
    return {
        "name": "Reset",
        "firstname": "Test",
        "username": f"{prefix}_{n}",
        "password": "Test@1234!",
        "mail": f"{prefix}_{n}@example.com",
    }


async def _register(client, payload: dict) -> dict:
    resp = await client.post("/user/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _login(client, username: str, password: str) -> dict:
    resp = await client.post(
        "/user/login", json={"username": username, "password": password}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Forgot
# ---------------------------------------------------------------------------


async def test_forgot_existing_address_returns_202(client):
    payload = _unique_user("forgot")
    await _register(client, payload)

    with patch("app.routes.user.send_mail", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/user/password/forgot", json={"mail": payload["mail"]}
        )
    assert resp.status_code == 202


async def test_forgot_unknown_address_still_returns_202(client):
    """Enumeration protection — must not distinguish known from unknown addresses."""
    resp = await client.post(
        "/user/password/forgot", json={"mail": "nobody_at_all@example.com"}
    )
    assert resp.status_code == 202


async def test_forgot_sends_email_with_reset_link(client):
    payload = _unique_user("link")
    await _register(client, payload)

    captured = {}

    async def _capture(to, subject, body, html=None):
        captured["to"] = to
        captured["subject"] = subject
        captured["body"] = body
        return True

    with patch("app.routes.user.send_mail", side_effect=_capture):
        resp = await client.post(
            "/user/password/forgot", json={"mail": payload["mail"]}
        )
    assert resp.status_code == 202
    assert captured.get("to") == payload["mail"]
    assert "reset-password" in captured.get("body", "")
    assert "token=" in captured.get("body", "")


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------


async def _get_reset_token(client, mail: str) -> str:
    """Trigger forgot and capture the raw token from the emailed link."""
    token_holder = {}

    async def _capture(to, subject, body, html=None):
        # Link: {FRONTEND_URL}/reset-password?token=<token>\n
        if "token=" in body:
            token_holder["token"] = body.split("token=")[1].split()[0].strip()
        return True

    with patch("app.routes.user.send_mail", side_effect=_capture):
        await client.post("/user/password/forgot", json={"mail": mail})

    return token_holder["token"]


async def test_reset_changes_password(client):
    payload = _unique_user("reset")
    await _register(client, payload)

    token = await _get_reset_token(client, payload["mail"])

    resp = await client.post(
        "/user/password/reset",
        json={"token": token, "password": "NewPass@9876!"},
    )
    assert resp.status_code == 204

    # Old password no longer works
    resp = await client.post(
        "/user/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert resp.status_code == 401

    # New password works
    resp = await client.post(
        "/user/login",
        json={"username": payload["username"], "password": "NewPass@9876!"},
    )
    assert resp.status_code == 200


async def test_reset_token_is_single_use(client):
    payload = _unique_user("once")
    await _register(client, payload)

    token = await _get_reset_token(client, payload["mail"])

    # First use succeeds
    r1 = await client.post(
        "/user/password/reset",
        json={"token": token, "password": "FirstNew@1!"},
    )
    assert r1.status_code == 204

    # Replay is rejected
    r2 = await client.post(
        "/user/password/reset",
        json={"token": token, "password": "SecondNew@2!"},
    )
    assert r2.status_code == 400


async def test_reset_invalid_token_returns_400(client):
    resp = await client.post(
        "/user/password/reset",
        json={"token": "this-token-was-never-issued", "password": "Valid@1234!"},
    )
    assert resp.status_code == 400


async def test_reset_kills_existing_sessions(client):
    """The security invariant: a reset must invalidate the attacker's tokens."""
    payload = _unique_user("killsess")
    await _register(client, payload)

    # Log in and obtain a refresh token
    tokens = await _login(client, payload["username"], payload["password"])

    token = await _get_reset_token(client, payload["mail"])

    resp = await client.post(
        "/user/password/reset",
        json={"token": token, "password": "AfterReset@1!"},
    )
    assert resp.status_code == 204

    # The pre-reset refresh token must now be dead
    resp = await client.post(
        "/user/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 401


async def test_reset_weak_password_rejected(client):
    payload = _unique_user("weakpw")
    await _register(client, payload)

    token = await _get_reset_token(client, payload["mail"])

    resp = await client.post(
        "/user/password/reset",
        json={"token": token, "password": "weak"},
    )
    assert resp.status_code == 422
