"""Shared limit/offset pagination for list endpoints."""

from typing import Any, Callable, Iterable

from fastapi import Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.schemas.classes import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


def limit_param(default: int = DEFAULT_PAGE_SIZE) -> Any:
    return Query(
        default=default,
        ge=1,
        le=MAX_PAGE_SIZE,
        description=f"Maximum rows to return (1-{MAX_PAGE_SIZE})",
    )


def offset_param() -> Any:
    return Query(default=0, ge=0, description="Rows to skip")


async def paginate(
    session: AsyncSession,
    stmt: Select,
    limit: int,
    offset: int,
    transform: Callable[[Any], Any] | None = None,
) -> dict:
    """Run `stmt` as one page and report how many rows matched in total.

    The count is taken from the same statement with its ordering stripped —
    ORDER BY is meaningless inside a COUNT subquery and MariaDB rejects some
    forms of it. `selectinload` options ride along harmlessly: they emit their
    own follow-up queries rather than changing this statement's columns.
    """
    total = await session.scalar(
        select(func.count()).select_from(stmt.order_by(None).subquery())
    )
    result = await session.execute(stmt.limit(limit).offset(offset))
    rows: Iterable[Any] = result.scalars().all()
    return {
        "items": [transform(r) for r in rows] if transform else list(rows),
        "total": total or 0,
        "limit": limit,
        "offset": offset,
    }
