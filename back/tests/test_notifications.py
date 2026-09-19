"""Integration tests for the notification write-path.

Before this, `notifications` had no writer at all — every read endpoint was
guaranteed to return nothing. These cover creation, the RBAC gates on it, the
broadcast audience, and the event lifecycle hooks.
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
        "name": "Notif",
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


async def _messages(client, tokens: dict) -> list[str]:
    resp = await client.get("/user/notification/", headers=_auth(tokens))
    assert resp.status_code == 200, resp.text
    return [n["message"] for n in resp.json()]


async def _create_event(client, tokens: dict, title: str) -> dict:
    start = datetime.now(timezone.utc) + timedelta(days=3)
    resp = await client.post(
        "/event/",
        headers=_auth(tokens),
        json={
            "title": title,
            "description": "d",
            "start_date": start.isoformat(),
            "end_date": (start + timedelta(hours=1)).isoformat(),
            "registrations_limits": 10,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# POST /user/notification/
# ---------------------------------------------------------------------------


async def test_staff_can_send_a_notification_and_recipient_sees_it(client, db_session):
    sender, sender_tokens = await _register_and_login(client, "nsender")
    await _grant(db_session, sender["id"], "staff")
    recipient, recipient_tokens = await _register_and_login(client, "nrecipient")

    resp = await client.post(
        "/user/notification/",
        headers=_auth(sender_tokens),
        json={"user_id": recipient["id"], "message": "hello there"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["message"] == "hello there"
    assert body["read"] is False
    assert body["from_id"] == sender["id"], "from_id must record who sent it"

    assert "hello there" in await _messages(client, recipient_tokens)


async def test_notification_goes_only_to_its_recipient(client, db_session):
    sender, sender_tokens = await _register_and_login(client, "nscope_send")
    await _grant(db_session, sender["id"], "staff")
    recipient, _ = await _register_and_login(client, "nscope_to")
    _, bystander_tokens = await _register_and_login(client, "nscope_other")

    resp = await client.post(
        "/user/notification/",
        headers=_auth(sender_tokens),
        json={"user_id": recipient["id"], "message": "for recipient only"},
    )
    assert resp.status_code == 201

    assert "for recipient only" not in await _messages(client, bystander_tokens)


async def test_plain_member_cannot_send_notifications(client):
    _, member_tokens = await _register_and_login(client, "nmember")
    other, _ = await _register_and_login(client, "ntarget")

    resp = await client.post(
        "/user/notification/",
        headers=_auth(member_tokens),
        json={"user_id": other["id"], "message": "spam"},
    )
    assert resp.status_code == 403


async def test_sending_to_unknown_user_is_404(client, db_session):
    sender, tokens = await _register_and_login(client, "n404")
    await _grant(db_session, sender["id"], "staff")

    resp = await client.post(
        "/user/notification/",
        headers=_auth(tokens),
        json={"user_id": 999_999, "message": "nobody"},
    )
    assert resp.status_code == 404


async def test_empty_message_is_rejected(client, db_session):
    sender, tokens = await _register_and_login(client, "nempty")
    await _grant(db_session, sender["id"], "staff")
    target, _ = await _register_and_login(client, "nempty_to")

    resp = await client.post(
        "/user/notification/",
        headers=_auth(tokens),
        json={"user_id": target["id"], "message": ""},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------


async def test_broadcast_to_a_role_reaches_only_that_role(client, db_session):
    admin, admin_tokens = await _register_and_login(client, "bcast_admin")
    await _grant(db_session, admin["id"], "admin")

    staffer, staff_tokens = await _register_and_login(client, "bcast_staff")
    await _grant(db_session, staffer["id"], "staff")

    _, member_tokens = await _register_and_login(client, "bcast_member")

    resp = await client.post(
        "/user/notification/broadcast",
        headers=_auth(admin_tokens),
        json={"message": "staff meeting at noon", "role": "staff"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["sent"] >= 1

    assert "staff meeting at noon" in await _messages(client, staff_tokens)
    assert "staff meeting at noon" not in await _messages(client, member_tokens)


async def test_broadcast_without_a_role_reaches_everyone(client, db_session):
    admin, admin_tokens = await _register_and_login(client, "bcast_all_admin")
    await _grant(db_session, admin["id"], "admin")
    _, member_tokens = await _register_and_login(client, "bcast_all_member")

    resp = await client.post(
        "/user/notification/broadcast",
        headers=_auth(admin_tokens),
        json={"message": "server maintenance tonight"},
    )
    assert resp.status_code == 201, resp.text

    assert "server maintenance tonight" in await _messages(client, member_tokens)


async def test_staff_cannot_broadcast(client, db_session):
    staffer, tokens = await _register_and_login(client, "bcast_denied")
    await _grant(db_session, staffer["id"], "staff")

    resp = await client.post(
        "/user/notification/broadcast",
        headers=_auth(tokens),
        json={"message": "should not go out"},
    )
    assert resp.status_code == 403, "broadcast is admin-only"


# ---------------------------------------------------------------------------
# Mark-all-read
# ---------------------------------------------------------------------------


async def test_read_all_marks_everything_and_is_idempotent(client, db_session):
    sender, sender_tokens = await _register_and_login(client, "readall_send")
    await _grant(db_session, sender["id"], "staff")
    recipient, recipient_tokens = await _register_and_login(client, "readall_to")

    for i in range(2):
        resp = await client.post(
            "/user/notification/",
            headers=_auth(sender_tokens),
            json={"user_id": recipient["id"], "message": f"msg {i}"},
        )
        assert resp.status_code == 201

    resp = await client.put(
        "/user/notification/read-all", headers=_auth(recipient_tokens)
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["sent"] == 2

    resp = await client.get("/user/notification/", headers=_auth(recipient_tokens))
    assert all(n["read"] for n in resp.json())

    # Second call changes nothing, so it reports 0 rather than the total.
    resp = await client.put(
        "/user/notification/read-all", headers=_auth(recipient_tokens)
    )
    assert resp.json()["sent"] == 0


# ---------------------------------------------------------------------------
# Event lifecycle hooks
# ---------------------------------------------------------------------------


async def test_registering_for_an_event_notifies_the_registrant(client, db_session):
    staffer, staff_tokens = await _register_and_login(client, "evn_staff")
    await _grant(db_session, staffer["id"], "staff")
    _, member_tokens = await _register_and_login(client, "evn_member")

    event = await _create_event(client, staff_tokens, "Bowling night")
    resp = await client.post(
        f"/event/{event['id']}/register", headers=_auth(member_tokens)
    )
    assert resp.status_code == 204, resp.text

    assert any(
        "Bowling night" in m for m in await _messages(client, member_tokens)
    ), "registrant should get a confirmation"


async def test_updating_an_event_notifies_registrants(client, db_session):
    staffer, staff_tokens = await _register_and_login(client, "evu_staff")
    await _grant(db_session, staffer["id"], "staff")
    _, member_tokens = await _register_and_login(client, "evu_member")

    event = await _create_event(client, staff_tokens, "Quiz evening")
    assert (
        await client.post(
            f"/event/{event['id']}/register", headers=_auth(member_tokens)
        )
    ).status_code == 204

    resp = await client.put(
        f"/event/{event['id']}",
        headers=_auth(staff_tokens),
        json={"description": "now with prizes"},
    )
    assert resp.status_code == 200, resp.text

    assert any("has been updated" in m for m in await _messages(client, member_tokens))


async def test_cancelling_an_event_notifies_registrants(client, db_session):
    admin, admin_tokens = await _register_and_login(client, "evd_admin")
    await _grant(db_session, admin["id"], "admin")
    _, member_tokens = await _register_and_login(client, "evd_member")

    event = await _create_event(client, admin_tokens, "Cancelled outing")
    assert (
        await client.post(
            f"/event/{event['id']}/register", headers=_auth(member_tokens)
        )
    ).status_code == 204

    resp = await client.delete(f"/event/{event['id']}", headers=_auth(admin_tokens))
    assert resp.status_code == 204, resp.text

    messages = await _messages(client, member_tokens)
    assert any("has been cancelled" in m for m in messages)
    assert any(
        "Cancelled outing" in m for m in messages
    ), "the title must be captured before the row is deleted"


async def test_event_notification_failure_does_not_break_registration(
    client, db_session, monkeypatch
):
    """A courtesy notification must never turn a successful action into a 500.

    The failure is injected *inside* the helper rather than by replacing it, so
    this exercises the real error handling. A plain RuntimeError also proves the
    catch is not narrowed to SQLAlchemyError — a driver or connection failure
    would not be one.
    """
    staffer, staff_tokens = await _register_and_login(client, "evfail_staff")
    await _grant(db_session, staffer["id"], "staff")
    _, member_tokens = await _register_and_login(client, "evfail_member")

    event = await _create_event(client, staff_tokens, "Resilient event")

    def _explode(*args, **kwargs):
        raise RuntimeError("notification insert exploded")

    monkeypatch.setattr("app.core.notifications.Notification", _explode)

    resp = await client.post(
        f"/event/{event['id']}/register", headers=_auth(member_tokens)
    )
    assert resp.status_code == 204, "registration must still succeed"

    monkeypatch.undo()

    # The registration is genuinely persisted, not merely reported as a 204.
    resp = await client.get("/event/?my_events=true", headers=_auth(member_tokens))
    assert any(
        e["id"] == event["id"] for e in resp.json()
    ), "and must actually be persisted"

    # ...and no notification was stored for it.
    assert not any(
        "Resilient event" in m for m in await _messages(client, member_tokens)
    )


async def test_broadcast_survives_a_notification_failure(
    client, db_session, monkeypatch
):
    """The admin-facing broadcast reports 0 sent rather than 500-ing."""
    admin, tokens = await _register_and_login(client, "bcastfail_admin")
    await _grant(db_session, admin["id"], "admin")

    def _explode(*args, **kwargs):
        raise RuntimeError("notification insert exploded")

    monkeypatch.setattr("app.core.notifications.Notification", _explode)

    resp = await client.post(
        "/user/notification/broadcast",
        headers=_auth(tokens),
        json={"message": "will not land"},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["sent"] == 0
