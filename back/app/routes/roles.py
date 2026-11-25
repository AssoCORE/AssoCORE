"""Role list and role assignment (R1).

Only admins assign roles. The rules themselves (`member` kept, last admin
protected, unknown names refused) live in `core/roles.py` `set_roles()`, the
only writer of `user_roles`.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, require_admin
from app.core.pagination import limit_param, offset_param, paginate
from app.core.roles import LastAdmin, UnknownRoles, set_roles
from app.db import get_session
from app.db.models import Role, RoleChangeLog, User
from app.schemas.classes import Page, RoleOut, UserOut
from app.routes.user import _user_q
from app.schemas.roles import RoleChangeOut, RolesUpdate

# Every route needs a logged-in user; the admin-only ones add require_admin.
router = APIRouter(tags=["roles"], dependencies=[Depends(get_current_user)])

USER_NOT_FOUND = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
)


@router.get(
    "/role/",
    response_model=Page[RoleOut],
    summary="List the roles that exist, for labelling them",
)
async def list_roles(
    limit: int = limit_param(),
    offset: int = offset_param(),
    session: AsyncSession = Depends(get_session),
):
    return await paginate(session, select(Role).order_by(Role.id), limit, offset)


@router.put(
    "/user/{user_id}/roles",
    response_model=UserOut,
    summary="Set a user's roles (the full desired set)",
)
async def put_user_roles(
    user_id: int,
    body: RolesUpdate,
    admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
):
    user = (
        await session.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user_id)
        )
    ).scalar_one_or_none()
    if user is None:
        raise USER_NOT_FOUND

    try:
        await set_roles(session, user, body.roles, changed_by=admin.id)
    except UnknownRoles as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)
        )
    except LastAdmin as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    # Reload with everything UserOut reads: async sessions can't lazy-load.
    result = await session.execute(_user_q().where(User.id == user_id))
    return result.scalars().first()


@router.get(
    "/user/{user_id}/role-history",
    response_model=Page[RoleChangeOut],
    summary="A user's role grants and revocations, newest first",
    dependencies=[Depends(require_admin)],
)
async def get_role_history(
    user_id: int,
    limit: int = limit_param(),
    offset: int = offset_param(),
    session: AsyncSession = Depends(get_session),
):
    if await session.get(User, user_id) is None:
        raise USER_NOT_FOUND
    stmt = (
        select(RoleChangeLog)
        .options(selectinload(RoleChangeLog.role))
        .where(RoleChangeLog.user_id == user_id)
        .order_by(RoleChangeLog.created_at.desc(), RoleChangeLog.id.desc())
    )
    return await paginate(session, stmt, limit, offset)
