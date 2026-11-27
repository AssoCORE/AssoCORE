"""The authenticated user's data export (GDPR art. 15 and 20)."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.export import build_export
from app.db import get_session
from app.db.models import User

router = APIRouter(tags=["user"])


@router.get(
    "/user/me/export",
    summary="Download everything AssoCORE stores about you, as JSON",
)
async def export_me(
    response: Response,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    response.headers["Content-Disposition"] = (
        'attachment; filename="assocore-export.json"'
    )
    response.headers["Cache-Control"] = "no-store"
    return await build_export(session, current_user)
