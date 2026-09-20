import logging

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response

from app.core.crypto import decrypt_secret
from app.core.dependencies import get_current_user
from app.core.nextcloud import get_admin_nc
from app.db.database import get_session
from app.db.models import NextcloudAccount, User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

router = APIRouter(prefix="/avatar", tags=["avatar"])

# Keep this reasonably small. Nextcloud performs its own image validation,
# but we don't want the AssoCORE API to accept arbitrarily large uploads.
MAX_AVATAR_BYTES = 10 * 1024 * 1024
DEFAULT_AVATAR_SIZE = 512


def _nc_base_url() -> str:
    """
    Get the configured Nextcloud base URL from the existing admin client.

    Adjust this property if your get_admin_nc() implementation exposes the
    server URL under a different attribute.
    """
    nc = get_admin_nc()

    for attr in ("url", "base_url", "base_url"):
        value = getattr(nc, attr, None)
        if value:
            return str(value).rstrip("/")

    raise RuntimeError("Unable to determine Nextcloud base URL")


async def _get_nc_account(
    user: User,
    session: AsyncSession,
) -> NextcloudAccount:
    result = await session.execute(
        select(NextcloudAccount).where(NextcloudAccount.user_id == user.id)
    )
    account = result.scalars().first()

    if account is None or not account.app_password_enc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nextcloud account is not available",
        )

    return account


async def _nc_request(
    *,
    username: str,
    app_password: str,
    method: str,
    path: str,
    **kwargs,
) -> httpx.Response:
    """
    Perform an authenticated request against Nextcloud using the user's
    own app password.
    """
    url = f"{_nc_base_url()}/{path.lstrip('/')}"

    async with httpx.AsyncClient(
        auth=(username, app_password),
        timeout=20.0,
        follow_redirects=True,
    ) as client:
        return await client.request(method, url, **kwargs)


async def _avatar_response(
    user: User,
    session: AsyncSession,
    size: int = DEFAULT_AVATAR_SIZE,
) -> Response:
    account = await _get_nc_account(user, session)

    try:
        app_password = decrypt_secret(account.app_password_enc)

        response = await _nc_request(
            username=account.nc_username,
            app_password=app_password,
            method="GET",
            path=f"/index.php/avatar/{account.nc_username}/{size}",
        )
    except Exception:
        log.warning(
            "Failed to fetch Nextcloud avatar for %s",
            user.username,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nextcloud is unavailable",
        )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Avatar not found",
        )

    if response.status_code >= 400:
        log.warning(
            "Nextcloud avatar request failed for %s: HTTP %s",
            user.username,
            response.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to retrieve avatar",
        )

    media_type = response.headers.get("content-type", "image/png")

    headers = {}

    # Preserve Nextcloud's custom-avatar marker when present.
    custom_avatar = response.headers.get("X-NC-IsCustomAvatar")
    if custom_avatar is not None:
        headers["X-NC-IsCustomAvatar"] = custom_avatar

    return Response(
        content=response.content,
        media_type=media_type,
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Avatar
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    summary="Get the authenticated user's avatar",
    responses={
        200: {"content": {"image/*": {}}},
        404: {"description": "Avatar not found"},
    },
)
async def get_my_avatar(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    return await _avatar_response(current_user, session)


@router.get(
    "/{user_id}",
    summary="Get another user's avatar",
    responses={
        200: {"content": {"image/*": {}}},
        404: {"description": "User or avatar not found"},
    },
)
async def get_user_avatar(
    user_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    # Authentication is intentionally enough here. Nextcloud avatars are
    # readable to authenticated NC users, and the application-level policy
    # requested for this endpoint is "another member's avatar".
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return await _avatar_response(user, session)


@router.put(
    "/me",
    summary="Upload or replace the authenticated user's avatar",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def upload_my_avatar(
    file: UploadFile = File(..., description="Avatar image"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Avatar must be an image",
        )

    account = await _get_nc_account(current_user, session)

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar file is empty",
        )

    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Avatar must not exceed {MAX_AVATAR_BYTES // (1024 * 1024)} MB",
        )

    try:
        app_password = decrypt_secret(account.app_password_enc)

        response = await _nc_request(
            username=account.nc_username,
            app_password=app_password,
            method="POST",
            path="/index.php/avatar/",
            files={
                "files": (
                    file.filename or "avatar",
                    content,
                    file.content_type,
                )
            },
        )
    except Exception:
        log.warning(
            "Failed to upload Nextcloud avatar for %s",
            current_user.username,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nextcloud is unavailable",
        )

    if response.status_code >= 400:
        log.warning(
            "Nextcloud avatar upload failed for %s: HTTP %s: %s",
            current_user.username,
            response.status_code,
            response.text[:500],
        )

        # Nextcloud normally returns a 400 for invalid image data.
        if response.status_code == 400:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid avatar image",
            )

        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Nextcloud rejected the user's credentials",
            )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update avatar",
        )


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Reset the authenticated user's avatar",
)
async def delete_my_avatar(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    account = await _get_nc_account(current_user, session)

    try:
        app_password = decrypt_secret(account.app_password_enc)

        response = await _nc_request(
            username=account.nc_username,
            app_password=app_password,
            method="DELETE",
            path="/index.php/avatar/",
        )
    except Exception:
        log.warning(
            "Failed to delete Nextcloud avatar for %s",
            current_user.username,
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Nextcloud is unavailable",
        )

    if response.status_code >= 400:
        log.warning(
            "Nextcloud avatar deletion failed for %s: HTTP %s: %s",
            current_user.username,
            response.status_code,
            response.text[:500],
        )

        if response.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Nextcloud rejected the user's credentials",
            )

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reset avatar",
        )
