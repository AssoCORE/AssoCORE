"""Role assignment (R1): who may assign, the rules, the audit log, hooks, GDPR."""

import itertools
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import selectinload

from app.core import roles as roles_mod
from app.core.roles import purge_role_history
from app.db.models import Notification, Role, RoleChangeLog, User, user_roles

_counter = itertools.count(1)


async def _register_and_login(client, prefix: str) -> tuple[dict, dict]:
    n = next(_counter)
    payload = {
        "name": "Role",
        "firstname": "Test",
        "username": f"{prefix}_{n}",
        "password": "Test@1234!",
        "mail": f"{prefix}_{n}@example.com",
    }
    resp = await client.post("/user/", json=payload)
    assert resp.status_code == 201, resp.text
    resp = await client.post(
        "/user/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    assert resp.status_code == 200, resp.text
    me = await client.get(
        "/user/me", headers={"Authorization": f"Bearer {resp.json()['access_token']}"}
    )
    return me.json(), resp.json()


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _grant(db_session, user_id: int, role_name: str) -> None:
    """Seed a role directly, bypassing set_roles (test setup only)."""
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


async def _admin(client, db_session, prefix: str = "admin") -> tuple[dict, dict]:
    user, tokens = await _register_and_login(client, prefix)
    await _grant(db_session, user["id"], "admin")
    return user, tokens


async def _put_roles(client, tokens: dict, user_id: int, roles: list[str]):
    return await client.put(
        f"/user/{user_id}/roles", json={"roles": roles}, headers=_auth(tokens)
    )


def _names(user_json: dict) -> set[str]:
    return {r["name"] for r in user_json["roles"]}


async def _history_count(db_session, user_id: int) -> int:
    return (
        await db_session.execute(
            select(func.count())
            .select_from(RoleChangeLog)
            .where(RoleChangeLog.user_id == user_id)
        )
    ).scalar_one()


@pytest.fixture
def hooks():
    """Register test hooks for one test only."""
    added = []

    def register(fn):
        roles_mod.on_roles_changed(fn)
        added.append(fn)
        return fn

    yield register
    for fn in added:
        roles_mod._hooks.remove(fn)


# --- GET /role/ ---


async def test_any_logged_in_user_can_list_roles(client):
    _, tokens = await _register_and_login(client, "lister")
    resp = await client.get("/role/", headers=_auth(tokens))
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert {"admin", "staff", "member"} <= {r["name"] for r in body["items"]}
    assert body["total"] >= 3


async def test_listing_roles_requires_login(client):
    assert (await client.get("/role/")).status_code in (401, 403)


# --- who may assign ---


@pytest.mark.parametrize("actor_role", [None, "staff"], ids=["member", "staff"])
async def test_only_admins_assign_roles(client, db_session, actor_role):
    actor, tokens = await _register_and_login(client, "actor")
    if actor_role:
        await _grant(db_session, actor["id"], actor_role)
    target, _ = await _register_and_login(client, "target")

    resp = await _put_roles(client, tokens, target["id"], ["staff"])
    assert resp.status_code == 403
    # Not even on themselves.
    resp = await _put_roles(client, tokens, actor["id"], ["admin"])
    assert resp.status_code == 403
    assert await _history_count(db_session, target["id"]) == 0


async def test_unknown_user_is_404(client, db_session):
    _, tokens = await _admin(client, db_session)
    assert (await _put_roles(client, tokens, 999_999, ["staff"])).status_code == 404


# --- the rules ---


async def test_admin_grants_a_role(client, db_session):
    admin, tokens = await _admin(client, db_session)
    target, target_tokens = await _register_and_login(client, "grantee")

    resp = await _put_roles(client, tokens, target["id"], ["member", "staff"])
    assert resp.status_code == 200, resp.text
    assert _names(resp.json()) == {"member", "staff"}

    # Effective on the very next request: roles are read from the DB each time.
    me = await client.get("/user/me", headers=_auth(target_tokens))
    assert _names(me.json()) == {"member", "staff"}

    # The user is told, and the notification is attributed to the admin.
    notes = (
        (
            await db_session.execute(
                select(Notification).where(Notification.user_id == target["id"])
            )
        )
        .scalars()
        .all()
    )
    assert [(n.message, n.from_id) for n in notes] == [
        ("Vous avez maintenant le rôle Staff.", admin["id"])
    ]


async def test_member_is_always_kept(client, db_session):
    _, tokens = await _admin(client, db_session)
    target, _ = await _register_and_login(client, "keeper")

    resp = await _put_roles(client, tokens, target["id"], ["staff"])
    assert _names(resp.json()) == {"member", "staff"}

    resp = await _put_roles(client, tokens, target["id"], [])
    assert resp.status_code == 200
    assert _names(resp.json()) == {"member"}


async def test_unknown_role_is_422_and_changes_nothing(client, db_session):
    _, tokens = await _admin(client, db_session)
    target, _ = await _register_and_login(client, "unknown")

    resp = await _put_roles(client, tokens, target["id"], ["staff", "wizard"])
    assert resp.status_code == 422
    assert "wizard" in resp.json()["detail"]

    me = (await client.get(f"/user/{target['id']}", headers=_auth(tokens))).json()
    assert _names(me) == {"member"}
    assert await _history_count(db_session, target["id"]) == 0


async def test_last_admin_cannot_be_demoted(client, db_session):
    admin, tokens = await _admin(client, db_session, "solo")
    # Make them the only admin left in the shared test database.
    admin_role_id = (
        await db_session.execute(select(Role.id).where(Role.name == "admin"))
    ).scalar_one()
    await db_session.execute(
        delete(user_roles).where(
            user_roles.c.role_id == admin_role_id, user_roles.c.user_id != admin["id"]
        )
    )
    await db_session.commit()

    resp = await _put_roles(client, tokens, admin["id"], ["member"])
    assert resp.status_code == 409
    me = await client.get("/user/me", headers=_auth(tokens))
    assert "admin" in _names(me.json())

    # Once someone else is admin, they may step down.
    other, _ = await _register_and_login(client, "second")
    assert (await _put_roles(client, tokens, other["id"], ["admin"])).status_code == 200
    resp = await _put_roles(client, tokens, admin["id"], ["member"])
    assert resp.status_code == 200
    assert _names(resp.json()) == {"member"}


async def test_unchanged_roles_write_nothing(client, db_session, hooks):
    _, tokens = await _admin(client, db_session)
    target, _ = await _register_and_login(client, "noop")
    calls = []

    @hooks
    async def _record(session, change):
        calls.append(change)

    resp = await _put_roles(client, tokens, target["id"], ["member"])
    assert resp.status_code == 200
    assert await _history_count(db_session, target["id"]) == 0
    assert calls == []


# --- audit log ---


async def test_role_history_is_admin_only_and_newest_first(client, db_session):
    admin, tokens = await _admin(client, db_session)
    target, target_tokens = await _register_and_login(client, "audited")

    await _put_roles(client, tokens, target["id"], ["staff"])
    await _put_roles(client, tokens, target["id"], [])

    resp = await client.get(f"/user/{target['id']}/role-history", headers=_auth(tokens))
    assert resp.status_code == 200, resp.text
    page = resp.json()
    assert page["total"] == 2
    assert [(c["action"], c["role"]["name"]) for c in page["items"]] == [
        ("revoke", "staff"),
        ("grant", "staff"),
    ]
    assert all(c["changed_by"] == admin["id"] for c in page["items"])

    denied = await client.get(
        f"/user/{target['id']}/role-history", headers=_auth(target_tokens)
    )
    assert denied.status_code == 403


# --- hooks ---


async def test_hooks_run_after_the_commit(client, db_session, hooks):
    _, tokens = await _admin(client, db_session)
    target, _ = await _register_and_login(client, "hooked")
    seen = []

    @hooks
    async def _check(session, change):
        # Rolling back here would undo the change if it weren't committed yet.
        await session.rollback()
        held = (
            (
                await session.execute(
                    select(Role.name)
                    .join(user_roles, user_roles.c.role_id == Role.id)
                    .where(user_roles.c.user_id == change.user_id)
                )
            )
            .scalars()
            .all()
        )
        seen.append((change.granted, change.revoked, set(held)))

    resp = await _put_roles(client, tokens, target["id"], ["staff"])
    assert resp.status_code == 200
    assert seen == [(frozenset({"staff"}), frozenset(), {"member", "staff"})]


async def test_a_failing_hook_does_not_undo_the_change(client, db_session, hooks):
    _, tokens = await _admin(client, db_session)
    target, target_tokens = await _register_and_login(client, "boom")

    @hooks
    async def _explode(session, change):
        raise RuntimeError("feature sync is down")

    resp = await _put_roles(client, tokens, target["id"], ["staff"])
    assert resp.status_code == 200
    assert _names(resp.json()) == {"member", "staff"}
    me = await client.get("/user/me", headers=_auth(target_tokens))
    assert _names(me.json()) == {"member", "staff"}


# --- GDPR ---


async def test_erasure_deletes_own_history_and_detaches_authored_rows(
    client, db_session
):
    admin, admin_tokens = await _admin(client, db_session)
    other_admin, other_tokens = await _admin(client, db_session)
    erased, _ = await _register_and_login(client, "erased")
    bystander, _ = await _register_and_login(client, "bystander")

    await _put_roles(client, admin_tokens, erased["id"], ["staff"])
    await _put_roles(client, admin_tokens, bystander["id"], ["staff"])

    # Deleting a member removes their own history.
    resp = await client.delete(f"/user/{erased['id']}", headers=_auth(other_tokens))
    assert resp.status_code == 204
    assert await _history_count(db_session, erased["id"]) == 0

    # Deleting the admin keeps the history they wrote about someone else,
    # detached from their account.
    resp = await client.delete("/user/me", headers=_auth(admin_tokens))
    assert resp.status_code == 204
    db_session.expire_all()
    rows = (
        (
            await db_session.execute(
                select(RoleChangeLog).where(RoleChangeLog.user_id == bystander["id"])
            )
        )
        .scalars()
        .all()
    )
    assert len(rows) == 1
    assert rows[0].changed_by is None


async def test_purge_drops_rows_past_retention(db_session):
    user = User(
        name="P",
        firstname="P",
        username="purge_target",
        password="x",
        mail="purge_target@example.com",
    )
    db_session.add(user)
    await db_session.flush()
    role_id = (
        await db_session.execute(select(Role.id).where(Role.name == "staff"))
    ).scalar_one()
    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            RoleChangeLog(
                user_id=user.id,
                role_id=role_id,
                action="grant",
                created_at=now - timedelta(days=30 * 24 + 1),
            ),
            RoleChangeLog(
                user_id=user.id,
                role_id=role_id,
                action="revoke",
                created_at=now - timedelta(days=30 * 24 - 1),
            ),
        ]
    )
    await db_session.commit()

    purged = await purge_role_history(db_session, months=24, now=now)

    assert purged == 1
    remaining = (
        (
            await db_session.execute(
                select(RoleChangeLog.action).where(RoleChangeLog.user_id == user.id)
            )
        )
        .scalars()
        .all()
    )
    assert remaining == ["revoke"]


# --- export and the daily purge job ---


async def test_export_contains_own_role_history_without_the_admin(
    client, db_session
):
    _, admin_tokens = await _admin(client, db_session)
    member, member_tokens = await _register_and_login(client, "exported")
    other, _ = await _register_and_login(client, "notme")
    await _put_roles(client, admin_tokens, member["id"], ["staff"])
    await _put_roles(client, admin_tokens, other["id"], ["staff"])

    resp = await client.get("/user/me/export", headers=_auth(member_tokens))

    assert resp.status_code == 200, resp.text
    assert "attachment" in resp.headers["content-disposition"]
    body = resp.json()
    assert body["user_id"] == member["id"]
    assert body["profile"]["username"] == member["username"]
    assert "password" not in body["profile"]
    assert sorted(body["profile"]["roles"]) == ["member", "staff"]
    history = body["role_history"]
    assert [(h["role"], h["action"]) for h in history] == [("staff", "grant")]
    assert "changed_by" not in history[0]


async def test_export_requires_login(client):
    assert (await client.get("/user/me/export")).status_code in (401, 403)


async def test_the_worker_runs_the_purge_daily(db_session):
    from contextlib import asynccontextmanager

    from app.core import worker as worker_mod
    from app.core.worker import Worker

    job = worker_mod._pollers["purge_role_history"]
    assert job.every == timedelta(days=1)

    user = User(
        name="P", firstname="P", username="purge_job", password="x",
        mail="purge_job@example.com",
    )
    db_session.add(user)
    await db_session.flush()
    role_id = (
        await db_session.execute(select(Role.id).where(Role.name == "staff"))
    ).scalar_one()
    db_session.add(
        RoleChangeLog(
            user_id=user.id, role_id=role_id, action="grant",
            created_at=datetime.now(timezone.utc) - timedelta(days=30 * 24 + 1),
        )
    )
    await db_session.commit()

    @asynccontextmanager
    async def factory():
        yield db_session

    assert await Worker(factory, pollers={job.name: job}).run_once() >= 1
    assert await _history_count(db_session, user.id) == 0
