"""Pagination, search and the `my_events` filter on GET /event/.

`my_events` moved from a post-query Python filter to a SQL `.any()` clause —
without that, limit/offset would page over the unfiltered set and then discard
rows, so a page could come back short or empty while `total` disagreed.
"""

import itertools
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.models import Role, User

_counter = itertools.count(1)


def _unique_user(prefix: str) -> dict:
    n = next(_counter)
    return {
        "name": "Event",
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


async def _grant(db_session, user_id: int, role_name: str) -> None:
    user = (
        await db_session.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
    ).scalar_one()
    role = (
        await db_session.execute(select(Role).where(Role.name == role_name))
    ).scalar_one()
    user.roles.append(role)
    await db_session.commit()


async def _create_event(client, tokens: dict, title: str, days_ahead: int = 5) -> dict:
    start = datetime.now(timezone.utc) + timedelta(days=days_ahead)
    resp = await client.post(
        "/event/",
        headers=_auth(tokens),
        json={
            "title": title,
            "description": f"description for {title}",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(hours=2)).isoformat(),
            "registrations_limits": 10,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_event_list_returns_page_envelope(client, db_session):
    staff, tokens = await _register_and_login(client, "ev_env")
    await _grant(db_session, staff["id"], "staff")
    await _create_event(client, tokens, "envelope check")

    resp = await client.get("/event/", headers=_auth(tokens))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body) == {"items", "total", "limit", "offset"}
    assert body["total"] >= 1


async def test_event_search_and_slicing(client, db_session):
    staff, tokens = await _register_and_login(client, "ev_search")
    await _grant(db_session, staff["id"], "staff")

    marker = "zzsearchable"
    for i in range(3):
        await _create_event(client, tokens, f"{marker} {i}")

    resp = await client.get(f"/event/?q={marker}&limit=2", headers=_auth(tokens))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2

    resp = await client.get(
        f"/event/?q={marker}&limit=2&offset=2", headers=_auth(tokens)
    )
    assert len(resp.json()["items"]) == 1


async def test_my_events_filters_in_sql_so_paging_stays_consistent(client, db_session):
    staff, staff_tokens = await _register_and_login(client, "ev_owner")
    await _grant(db_session, staff["id"], "staff")

    member, member_tokens = await _register_and_login(client, "ev_member")

    mine = await _create_event(client, staff_tokens, "mine to attend")
    await _create_event(client, staff_tokens, "not mine")

    resp = await client.post(
        f"/event/{mine['id']}/register", headers=_auth(member_tokens)
    )
    assert resp.status_code == 204, resp.text

    resp = await client.get("/event/?my_events=true", headers=_auth(member_tokens))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["total"] == 1, "total must reflect the filter, not the whole table"
    assert [e["id"] for e in body["items"]] == [mine["id"]]

    # Someone who registered for nothing sees an empty page, not a short one.
    resp = await client.get("/event/?my_events=true", headers=_auth(staff_tokens))
    assert resp.json()["total"] == 0


async def test_event_upcoming_and_past_filters(client, db_session):
    staff, tokens = await _register_and_login(client, "ev_time")
    await _grant(db_session, staff["id"], "staff")

    marker = "zztimefilter"
    await _create_event(client, tokens, f"{marker} future", days_ahead=10)

    resp = await client.get(f"/event/?q={marker}&upcoming=true", headers=_auth(tokens))
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp = await client.get(f"/event/?q={marker}&past=true", headers=_auth(tokens))
    assert resp.json()["total"] == 0
