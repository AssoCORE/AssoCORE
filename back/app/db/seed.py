"""Idempotent startup seeding: default roles, a bootstrap admin, and a role backfill.

Runs from the app lifespan rather than from `init_db()` so `database.py` stays free of
password-hashing concerns.
"""

import logging
import os

from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.roles import DEFAULT_ROLES, ROLE_ADMIN, ROLE_MEMBER
from app.core.security import hash_password
from app.db.database import async_session
from app.db.models import Role, User

log = logging.getLogger(__name__)


async def seed_roles(session) -> None:
    result = await session.execute(
        select(Role.name).where(Role.name.in_(DEFAULT_ROLES))
    )
    existing = set(result.scalars().all())
    missing = [name for name in DEFAULT_ROLES if name not in existing]
    if not missing:
        return
    session.add_all([Role(name=name) for name in missing])
    try:
        await session.commit()
        log.info("Seeded roles: %s", ", ".join(missing))
    except IntegrityError:
        # Another replica won the race on the unique index — its rows are just as good.
        await session.rollback()


async def seed_admin_user(session) -> None:
    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD")
    if not password:
        log.warning(
            "ADMIN_PASSWORD is not set — skipping admin bootstrap. "
            "No user will hold the %r role until one is granted manually.",
            ROLE_ADMIN,
        )
        return

    admin_role = (
        (await session.execute(select(Role).where(Role.name == ROLE_ADMIN)))
        .scalars()
        .first()
    )
    if admin_role is None:
        log.warning("Role %r missing — cannot bootstrap the admin user", ROLE_ADMIN)
        return

    result = await session.execute(
        select(User).options(selectinload(User.roles)).where(User.username == username)
    )
    user = result.scalars().first()

    if user is not None:
        # Never touch an existing account's password — only make sure it is an admin.
        if admin_role not in user.roles:
            user.roles.append(admin_role)
            await session.commit()
            log.info("Granted %r the %r role", username, ROLE_ADMIN)
        return

    user = User(
        name=os.getenv("ADMIN_NAME", "Admin"),
        firstname=os.getenv("ADMIN_FIRSTNAME", "AssoCORE"),
        username=username,
        password=hash_password(password),
        mail=os.getenv("ADMIN_EMAIL", "admin@assocore.local"),
        roles=[admin_role],
    )
    session.add(user)
    try:
        await session.commit()
        log.info("Bootstrapped admin user %r", username)
    except IntegrityError:
        await session.rollback()


async def backfill_member_role(session) -> None:
    """Give role-less users the member role.

    Without this, everyone who registered before RBAC existed would silently fail any
    `require_roles` check.
    """
    member = (
        (await session.execute(select(Role).where(Role.name == ROLE_MEMBER)))
        .scalars()
        .first()
    )
    if member is None:
        return

    result = await session.execute(select(User).options(selectinload(User.roles)))
    patched = 0
    for user in result.scalars().all():
        if not user.roles:
            user.roles.append(member)
            patched += 1
    if patched:
        await session.commit()
        log.info("Backfilled the %r role onto %d user(s)", ROLE_MEMBER, patched)


async def seed_all() -> None:
    async with async_session() as session:
        await seed_roles(session)
        await seed_admin_user(session)
        await backfill_member_role(session)
