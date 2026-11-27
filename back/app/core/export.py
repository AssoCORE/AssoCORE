"""The user's data export, `GET /user/me/export` (GDPR art. 15 and 20).

Each feature that stores personal data contributes one section, registered next
to its own code, so the export grows with the features instead of in one route:

    @export_section("role_history")
    async def _export(session: AsyncSession, user: User) -> list[dict]:
        ...

A section returns plain JSON-able data about `user` only. It leaves out other
people's identities (who else was in a conversation, which admin made a
change) beyond what the user is entitled to see in the app itself.
"""

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

ExportSection = Callable[[AsyncSession, Any], Awaitable[Any]]
_sections: dict[str, ExportSection] = {}


def export_section(name: str):
    """Register `fn(session, user)` as the export's `name` section."""

    def decorate(fn: ExportSection) -> ExportSection:
        if name in _sections:
            raise ValueError(f"Export section {name!r} is already registered")
        _sections[name] = fn
        return fn

    return decorate


async def build_export(session: AsyncSession, user) -> dict:
    data: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_id": user.id,
    }
    for name, section in _sections.items():
        data[name] = await section(session, user)
    return data


@export_section("profile")
async def _profile(session: AsyncSession, user) -> dict:
    # Everything on the account except the password hash. `roles` must be loaded.
    return {
        "username": user.username,
        "firstname": user.firstname,
        "name": user.name,
        "mail": user.mail,
        "phone": user.phone,
        "birth_date": user.birth_date.isoformat() if user.birth_date else None,
        "roles": sorted(r.name for r in user.roles),
    }
