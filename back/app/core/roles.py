"""Role names, and the one place that changes who holds them.

`set_roles()` is the only code that writes `user_roles` outside the startup
seeder, just as `core/notifications.py` is the only writer of notifications.
Features that need to react to a role change (role chat channels, Nextcloud
groups and quotas, …) register an `on_roles_changed` hook here instead of being
imported by the routes.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Iterable

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

ROLE_ADMIN = "admin"
ROLE_STAFF = "staff"
ROLE_MEMBER = "member"

DEFAULT_ROLES = (ROLE_ADMIN, ROLE_STAFF, ROLE_MEMBER)

# Display names, for messages the backend writes itself (notifications). The
# frontend keeps its own copy in front/lib/roles.ts.
ROLE_LABELS = {
    ROLE_ADMIN: "Admin",
    ROLE_STAFF: "Staff",
    ROLE_MEMBER: "Membre",
}

# How long the role-change audit log is kept (GDPR art. 5(1)(e)). The default
# for the `role_audit_retention_months` setting, which #199 makes configurable.
ROLE_AUDIT_RETENTION_MONTHS = 24

log = logging.getLogger(__name__)


def label_of(role_name: str) -> str:
    return ROLE_LABELS.get(role_name, role_name)


# ---------------------------------------------------------------------------
# Errors — the routes map these to HTTP statuses
# ---------------------------------------------------------------------------


class RoleAssignmentError(Exception):
    """A role change that the rules refuse."""


class UnknownRoles(RoleAssignmentError):
    def __init__(self, names: Iterable[str]):
        self.names = sorted(names)
        super().__init__(f"Unknown role(s): {', '.join(self.names)}")


class LastAdmin(RoleAssignmentError):
    def __init__(self):
        super().__init__("The last admin cannot lose the admin role")


# ---------------------------------------------------------------------------
# Hooks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RoleChange:
    """What one `set_roles()` call changed, handed to every hook."""

    user_id: int
    granted: frozenset[str]
    revoked: frozenset[str]
    changed_by: int | None


RolesChangedHook = Callable[[AsyncSession, RoleChange], Awaitable[None]]
_hooks: list[RolesChangedHook] = []


def on_roles_changed(hook: RolesChangedHook) -> RolesChangedHook:
    """Register `hook` to run after every committed role change. Usable as a decorator.

    Hooks follow the notification contract: they run after the commit, are
    best-effort, and a failure is logged (by ID) and never undoes the change.
    Each feature's own reconcile job repairs what a failed hook missed.
    """
    _hooks.append(hook)
    return hook


async def _run_hooks(session: AsyncSession, change: RoleChange) -> None:
    for hook in list(_hooks):
        try:
            await hook(session, change)
        except Exception:
            # Same reasoning as core/notifications.py: the change is committed,
            # so a side effect failing must not turn it into a 500.
            log.warning(
                "on_roles_changed hook %s failed for user %d",
                getattr(hook, "__qualname__", hook),
                change.user_id,
                exc_info=True,
            )
            try:
                await session.rollback()
            except Exception:
                log.warning("Rollback after a failed role hook also failed")


# ---------------------------------------------------------------------------
# The writer
# ---------------------------------------------------------------------------


async def set_roles(
    session: AsyncSession,
    user,
    role_names: Iterable[str],
    changed_by: int | None,
) -> RoleChange:
    """Give `user` exactly `role_names` (plus `member`, which is never removed).

    `user` must have `roles` loaded. Validates, writes the roles and their audit
    rows, commits, then notifies the user and runs the `on_roles_changed` hooks.
    Raises `UnknownRoles` or `LastAdmin` before writing anything.

    Callers must check that the actor is allowed to assign roles: this function
    enforces the association's rules, not who may invoke them.
    """
    # Imported here so that importing a role name never pulls in the ORM.
    from app.core.notifications import notify
    from app.db.models import Role, RoleChangeLog, user_roles

    desired = set(role_names) | {ROLE_MEMBER}
    roles = (
        (await session.execute(select(Role).where(Role.name.in_(desired))))
        .scalars()
        .all()
    )
    unknown = desired - {r.name for r in roles}
    if unknown:
        raise UnknownRoles(unknown)

    # Captured now: a rollback in notify() or a hook expires `user`, and an
    # expired attribute can't be lazy-loaded on an async session.
    user_id = user.id
    current = {r.name for r in user.roles}
    granted = desired - current
    revoked = current - desired
    change = RoleChange(user_id, frozenset(granted), frozenset(revoked), changed_by)
    if not granted and not revoked:
        return change

    if ROLE_ADMIN in revoked:
        # Lock the admin rows so two admins demoting each other at the same time
        # can't both see "another admin exists" and leave none (MariaDB; SQLite
        # has no row locks and ignores FOR UPDATE).
        admin_id = next(r.id for r in user.roles if r.name == ROLE_ADMIN)
        other_admins = (
            await session.execute(
                select(func.count()).select_from(
                    select(user_roles.c.user_id)
                    .where(
                        user_roles.c.role_id == admin_id,
                        user_roles.c.user_id != user_id,
                    )
                    .with_for_update()
                    .subquery()
                )
            )
        ).scalar_one()
        if other_admins == 0:
            raise LastAdmin()

    by_name = {r.name: r for r in roles}
    by_name.update({r.name: r for r in user.roles})
    user.roles = [by_name[name] for name in sorted(desired)]
    session.add_all(
        [
            RoleChangeLog(
                user_id=user_id,
                role_id=by_name[name].id,
                action=action,
                changed_by=changed_by,
            )
            for action, names in (("grant", granted), ("revoke", revoked))
            for name in sorted(names)
        ]
    )
    await session.commit()
    log.info(
        "user %d roles changed by %s: +%d -%d",
        user_id,
        changed_by if changed_by is not None else "system",
        len(granted),
        len(revoked),
    )

    # Side effects, strictly after the commit.
    for name in sorted(granted):
        await notify(
            session,
            user_id,
            f"Vous avez maintenant le rôle {label_of(name)}.",
            changed_by,
        )
    for name in sorted(revoked):
        await notify(
            session, user_id, f"Vous n'avez plus le rôle {label_of(name)}.", changed_by
        )
    await _run_hooks(session, change)

    # Re-read so the caller gets the committed state (the hooks may have rolled
    # the session back, expiring `user`).
    await session.refresh(user)
    await session.refresh(user, ["roles"])
    return change


# ---------------------------------------------------------------------------
# GDPR: erasure and retention of the audit log
# ---------------------------------------------------------------------------


async def erase_role_history(session: AsyncSession, user_id: int) -> None:
    """Art. 17, called while deleting an account (the caller commits).

    The user's own history is deleted, and the rows they authored for other
    people are kept with `changed_by` set to NULL: deleting an account must
    never delete someone else's data. Done explicitly rather than relying on
    the foreign keys' ON DELETE, which SQLite does not enforce by default.
    """
    from app.db.models import RoleChangeLog

    await session.execute(delete(RoleChangeLog).where(RoleChangeLog.user_id == user_id))
    await session.execute(
        update(RoleChangeLog)
        .where(RoleChangeLog.changed_by == user_id)
        .values(changed_by=None)
    )


async def purge_role_history(
    session: AsyncSession,
    months: int = ROLE_AUDIT_RETENTION_MONTHS,
    now: datetime | None = None,
) -> int:
    """Delete audit rows older than `months` (30-day months). Returns how many.

    The retention purge for `role_changes`. The background worker (#217) runs
    it once the settings table (#199) supplies `role_audit_retention_months`.
    """
    from app.db.models import RoleChangeLog

    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=30 * months)
    result = await session.execute(
        delete(RoleChangeLog).where(RoleChangeLog.created_at < cutoff)
    )
    await session.commit()
    return result.rowcount or 0
