"""Integration tests for limit/offset pagination, search and filtering.

The in-memory DB is shared across the whole session, so these tests never assert
on a global row count. Instead each test tags its fixtures with a unique prefix
and filters by it, which keeps `total` deterministic no matter what other tests
have inserted.
"""

import itertools
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Notification, Role, User

_counter = itertools.count(1)


def _unique_user(prefix: str) -> dict:
    n = next(_counter)
    return {
        "name": "Page",
        "firstname": "Test",
        "username": f"{prefix}_{n}",
        "password": "Test@1234!",
        "mail": f"{prefix}_{n}@example.com",
    }


async def _register_and_login(client, prefix: str) -> tuple[dict, dict]:
    payload = _unique_user(prefix)
    resp = await client.post("/user/", json=payload)
    assert resp.status_code == 201, resp.text
    user = resp.json()
    resp = await client.post(
        "/user/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert resp.status_code == 200, resp.text
    return user, resp.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _make_admin(db_session, user_id: int) -> None:
    user = (
        await db_session.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
    ).scalar_one()
    admin_role = (
        await db_session.execute(select(Role).where(Role.name == "admin"))
    ).scalar_one()
    user.roles.append(admin_role)
    await db_session.commit()


# ---------------------------------------------------------------------------
# GET /user/  — envelope, slicing, search, role filter
# ---------------------------------------------------------------------------


async def test_user_list_returns_page_envelope(client, db_session):
    user, tokens = await _register_and_login(client, "env")
    await _make_admin(db_session, user["id"])

    resp = await client.get("/user/", headers=_auth(tokens))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert isinstance(body["items"], list)
    assert body["offset"] == 0


async def test_user_list_slices_but_total_counts_every_match(client, db_session):
    admin, tokens = await _register_and_login(client, "slice_admin")
    await _make_admin(db_session, admin["id"])

    prefix = "sliceme"
    for _ in range(3):
        payload = _unique_user(prefix)
        assert (await client.post("/user/", json=payload)).status_code == 201

    resp = await client.get(
        f"/user/?q={prefix}&limit=2&offset=0", headers=_auth(tokens)
    )
    assert resp.status_code == 200, resp.text
    first = resp.json()
    assert len(first["items"]) == 2
    # total is the count *before* limit/offset — the point of the envelope.
    assert first["total"] == 3

    resp = await client.get(
        f"/user/?q={prefix}&limit=2&offset=2", headers=_auth(tokens)
    )
    second = resp.json()
    assert len(second["items"]) == 1
    assert second["total"] == 3

    ids = {u["id"] for u in first["items"]} | {u["id"] for u in second["items"]}
    assert len(ids) == 3, "pages must not overlap"


async def test_user_search_matches_mail_and_is_case_insensitive(client, db_session):
    admin, tokens = await _register_and_login(client, "search_admin")
    await _make_admin(db_session, admin["id"])

    payload = _unique_user("findme")
    assert (await client.post("/user/", json=payload)).status_code == 201

    resp = await client.get("/user/?q=FINDME", headers=_auth(tokens))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all("findme" in u["username"] for u in body["items"])

    resp = await client.get("/user/?q=no_such_user_anywhere", headers=_auth(tokens))
    assert resp.json()["total"] == 0


async def test_user_role_filter(client, db_session):
    admin, tokens = await _register_and_login(client, "rolefilter")
    await _make_admin(db_session, admin["id"])

    resp = await client.get("/user/?role=admin", headers=_auth(tokens))
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert all(
        any(r["name"] == "admin" for r in u["roles"]) for u in body["items"]
    ), "role filter must only return holders of that role"

    resp = await client.get("/user/?role=no_such_role", headers=_auth(tokens))
    assert resp.json()["total"] == 0


async def test_user_list_rejects_out_of_range_limits(client, db_session):
    admin, tokens = await _register_and_login(client, "bounds")
    await _make_admin(db_session, admin["id"])

    assert (
        await client.get("/user/?limit=0", headers=_auth(tokens))
    ).status_code == 422
    assert (
        await client.get("/user/?limit=201", headers=_auth(tokens))
    ).status_code == 422
    assert (
        await client.get("/user/?offset=-1", headers=_auth(tokens))
    ).status_code == 422


async def test_user_list_still_admin_only(client):
    _, tokens = await _register_and_login(client, "notadmin")
    resp = await client.get("/user/", headers=_auth(tokens))
    assert resp.status_code == 403, "pagination must not have loosened the RBAC gate"


# ---------------------------------------------------------------------------
# GET /user/notification/  — unread filter drives the bell badge
# ---------------------------------------------------------------------------


async def test_notification_unread_filter_and_count(client, db_session):
    user, tokens = await _register_and_login(client, "notif")

    # No POST endpoint exists yet (that is issue #156), so seed directly.
    db_session.add_all(
        [
            Notification(user_id=user["id"], message="read one", read=True),
            Notification(user_id=user["id"], message="unread one", read=False),
            Notification(user_id=user["id"], message="unread two", read=False),
        ]
    )
    await db_session.commit()

    resp = await client.get("/user/notification/", headers=_auth(tokens))
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 3

    resp = await client.get(
        "/user/notification/?unread_only=true", headers=_auth(tokens)
    )
    body = resp.json()
    assert body["total"] == 2
    assert all(n["read"] is False for n in body["items"])

    # The bell badge pattern: ask for one row, read `total`.
    resp = await client.get(
        "/user/notification/?unread_only=true&limit=1", headers=_auth(tokens)
    )
    body = resp.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1


async def test_notifications_are_scoped_to_the_caller(client, db_session):
    owner, owner_tokens = await _register_and_login(client, "notif_owner")
    _, other_tokens = await _register_and_login(client, "notif_other")

    db_session.add(Notification(user_id=owner["id"], message="private"))
    await db_session.commit()

    resp = await client.get("/user/notification/", headers=_auth(other_tokens))
    assert resp.status_code == 200
    assert all(n["message"] != "private" for n in resp.json()["items"])


# ---------------------------------------------------------------------------
# GET /user/reminder/
# ---------------------------------------------------------------------------


async def test_reminder_upcoming_filter(client):
    _, tokens = await _register_and_login(client, "rem")
    now = datetime.now(timezone.utc)

    for when, title in (
        (now - timedelta(days=2), "past"),
        (now + timedelta(days=2), "future"),
    ):
        resp = await client.post(
            "/user/reminder/",
            headers=_auth(tokens),
            json={"date": when.isoformat(), "title": title},
        )
        assert resp.status_code == 201, resp.text

    resp = await client.get("/user/reminder/", headers=_auth(tokens))
    assert resp.json()["total"] == 2

    resp = await client.get("/user/reminder/?upcoming=true", headers=_auth(tokens))
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "future"
