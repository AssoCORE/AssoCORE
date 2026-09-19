"""Creating notifications.

Every caller here is a side effect of some *other* action — registering for an
event, an admin editing one. That action has already been committed by the time
these run, and they manage their own commit/rollback, so a notification that
fails to insert rolls back only itself and leaves the triggering action intact.
That is why nothing in this module raises: a user who successfully registered
for an event must not see a 500 because the courtesy notification failed.

Same posture as the best-effort Nextcloud calls in `routes/user.py`.
"""

import logging
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Notification, Role, User

log = logging.getLogger(__name__)


async def notify(
    session: AsyncSession,
    user_id: int,
    message: str,
    from_id: int | None = None,
) -> bool:
    """Send one notification. Returns whether it was stored.

    `from_id` is who caused it, or None when the system did.
    """
    return await notify_many(session, [user_id], message, from_id) == 1


async def notify_many(
    session: AsyncSession,
    user_ids: Iterable[int],
    message: str,
    from_id: int | None = None,
) -> int:
    """Send the same notification to several users. Returns how many were stored."""
    ids = list(dict.fromkeys(user_ids))  # de-duplicate, keep order
    if not ids:
        return 0

    try:
        session.add_all(
            [Notification(user_id=uid, message=message, from_id=from_id) for uid in ids]
        )
        await session.commit()
        return len(ids)
    except Exception:
        # Deliberately broad: a driver-level or connection error is not a
        # SQLAlchemyError, and letting one through would 500 a request whose
        # actual work already succeeded. `Exception` still lets BaseException
        # (CancelledError, KeyboardInterrupt) propagate, which it must.
        try:
            # Roll back only these rows — the trigger was committed already.
            await session.rollback()
        except Exception:
            log.warning("Rollback after a failed notification also failed")
        log.warning(
            "Failed to store notification for %d user(s)", len(ids), exc_info=True
        )
        return 0


async def notify_role(
    session: AsyncSession,
    role_name: str | None,
    message: str,
    from_id: int | None = None,
) -> int:
    """Notify every user, or every holder of `role_name` when one is given."""
    stmt = select(User.id)
    if role_name:
        stmt = stmt.where(User.roles.any(Role.name == role_name))
    try:
        result = await session.execute(stmt)
    except Exception:
        log.warning("Failed to resolve broadcast audience", exc_info=True)
        return 0
    return await notify_many(session, result.scalars().all(), message, from_id)
