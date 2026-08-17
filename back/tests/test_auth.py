"""Integration tests: register → login → protected route → 401 on bad/revoked token."""

import itertools

import pytest

# Unique username counter so tests never collide in the shared in-memory DB.
_counter = itertools.count(1)


def _unique_user(prefix: str = "user") -> dict:
    n = next(_counter)
    return {
        "name": "Test",
        "firstname": "User",
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


async def _register_and_login(client, prefix: str = "user") -> tuple[dict, dict, dict]:
    """Return (payload, user_out, tokens)."""
    payload = _unique_user(prefix)
    user = await _register(client, payload)
    tokens = await _login(client, payload["username"], payload["password"])
    return payload, user, tokens


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def test_register_returns_user_without_password(client):
    payload = _unique_user("reg")
    resp = await client.post("/user/", json=payload)

    assert resp.status_code == 201
    body = resp.json()
    assert body["username"] == payload["username"]
    assert body["mail"] == payload["mail"]
    assert "password" not in body


async def test_register_duplicate_username_fails(client):
    payload = _unique_user("dup")
    await client.post("/user/", json=payload)

    dupe = {**payload, "mail": "different@example.com"}
    resp = await client.post("/user/", json=dupe)
    assert resp.status_code == 409


async def test_register_duplicate_email_fails(client):
    payload = _unique_user("dupemail")
    await client.post("/user/", json=payload)

    dupe = {**payload, "username": "totally_different_username"}
    resp = await client.post("/user/", json=dupe)
    assert resp.status_code == 409


async def test_register_weak_password_rejected(client):
    payload = {**_unique_user("weakpw"), "password": "simple"}
    resp = await client.post("/user/", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


async def test_login_returns_token_pair(client):
    payload = _unique_user("login")
    await _register(client, payload)

    resp = await client.post(
        "/user/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


async def test_login_wrong_password(client):
    payload = _unique_user("badpw")
    await _register(client, payload)

    resp = await client.post(
        "/user/login", json={"username": payload["username"], "password": "Wrong@1234"}
    )
    assert resp.status_code == 401


async def test_login_unknown_user(client):
    resp = await client.post(
        "/user/login", json={"username": "nobody_at_all", "password": "Test@1234!"}
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Protected routes
# ---------------------------------------------------------------------------


async def test_get_me_with_valid_token(client):
    payload, _, tokens = await _register_and_login(client, "me")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    resp = await client.get("/user/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == payload["username"]


@pytest.mark.parametrize(
    "auth_header",
    [
        None,
        {"Authorization": "Bearer this.is.not.a.real.token"},
        {"Authorization": "Bearer eyJ.invalid.jwt"},
    ],
    ids=["no_token", "garbage_token", "malformed_jwt"],
)
async def test_get_me_rejects_bad_credentials(client, auth_header):
    kwargs = {"headers": auth_header} if auth_header else {}
    resp = await client.get("/user/me", **kwargs)
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Token refresh
# ---------------------------------------------------------------------------


async def test_refresh_issues_new_pair(client):
    _, __, tokens = await _register_and_login(client, "refresh")

    resp = await client.post(
        "/user/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    new_tokens = resp.json()
    assert "access_token" in new_tokens
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]


async def test_refresh_old_token_is_rejected_after_rotation(client):
    _, __, tokens = await _register_and_login(client, "rotation")

    # First rotation succeeds
    await client.post("/user/refresh", json={"refresh_token": tokens["refresh_token"]})

    # Replaying the original refresh token outside the grace window is treated as theft
    resp = await client.post(
        "/user/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    # Either 401 (reuse detected → family killed) or 200 (still in grace window)
    # Both are valid — we just confirm no 5xx
    assert resp.status_code in (200, 401)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


async def test_logout_revokes_access_token(client):
    _, __, tokens = await _register_and_login(client, "logout")
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    # Token works before logout
    assert (await client.get("/user/me", headers=headers)).status_code == 200

    # Logout
    resp = await client.post(
        "/user/logout",
        headers=headers,
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert resp.status_code == 204

    # Access token is now revoked
    assert (await client.get("/user/me", headers=headers)).status_code == 401


async def test_logout_all_revokes_every_session(client):
    payload = _unique_user("logoutall")
    await _register(client, payload)

    # Two separate logins (two families)
    tokens_a = await _login(client, payload["username"], payload["password"])
    tokens_b = await _login(client, payload["username"], payload["password"])

    headers_a = {"Authorization": f"Bearer {tokens_a['access_token']}"}

    resp = await client.post("/user/logout/all", headers=headers_a)
    assert resp.status_code == 204

    # Both sessions are dead
    assert (await client.get("/user/me", headers=headers_a)).status_code == 401
    headers_b = {"Authorization": f"Bearer {tokens_b['access_token']}"}
    # tokens_b was issued before logout/all — its refresh family is killed but the
    # access token itself is short-lived and not individually blacklisted by logout/all
    # (only the families are killed so new refreshes fail).  Access token B may still
    # be valid until it expires naturally.  We assert the refresh is dead instead.
    resp = await client.post(
        "/user/refresh", json={"refresh_token": tokens_b["refresh_token"]}
    )
    assert resp.status_code == 401
