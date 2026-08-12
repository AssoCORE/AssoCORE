"""Link an AssoCORE account to a real Nextcloud account via Login Flow v2.

The user approves the link in a browser and Nextcloud hands back an app password scoped to
this client. That password is per-user and revocable from Nextcloud's own settings, unlike
the SECRET_KEY-derived fallback in `core.nextcloud.derive_nc_password`.
"""

import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from nc_py_api import AsyncNextcloud
from redis.exceptions import RedisError
from sqlalchemy.future import select

from app.core.crypto import encrypt_secret
from app.core.dependencies import get_current_user
from app.core.nextcloud import nc_url, to_public_url
from app.core.redis_client import get_redis
from app.db.database import get_session
from app.db.models import NextcloudAccount, User
from app.schemas.classes import NcLinkInit, NcLinkPoll, NcLinkStatus
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger(__name__)

router = APIRouter(prefix="/nextcloud/link", tags=["nextcloud (link)"])

# Nextcloud expires a login flow after 20 minutes.
HANDLE_TTL = 20 * 60
HANDLE_PREFIX = "assocore:nclink:"

BACKEND_DOWN = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Link backend unavailable",
)


@router.post(
    "/init", response_model=NcLinkInit, summary="Start linking a Nextcloud account"
)
async def init_link(current_user: User = Depends(get_current_user)):
    nc = AsyncNextcloud(nextcloud_url=nc_url())
    try:
        flow = await nc.loginflow_v2.init(
            user_agent=f"AssoCORE ({current_user.username})"
        )
    except Exception as e:
        log.warning("Nextcloud login flow init failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not start the Nextcloud login flow",
        )

    # The poll token is bearer-equivalent: whoever holds it can claim the resulting app
    # password. Keep it server-side and hand the client an opaque handle instead.
    handle = secrets.token_urlsafe(32)
    try:
        redis = get_redis()
        await redis.hset(
            f"{HANDLE_PREFIX}{handle}",
            mapping={"user_id": str(current_user.id), "poll_token": flow.token},
        )
        await redis.expire(f"{HANDLE_PREFIX}{handle}", HANDLE_TTL)
    except RedisError:
        raise BACKEND_DOWN

    return NcLinkInit(
        login_url=to_public_url(flow.login),
        handle=handle,
        expires_in=HANDLE_TTL,
    )


@router.get(
    "/poll/{handle}",
    response_model=NcLinkPoll,
    summary="Check whether the user has approved the link yet",
)
async def poll_link(
    handle: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    try:
        data = await get_redis().hgetall(f"{HANDLE_PREFIX}{handle}")
    except RedisError:
        raise BACKEND_DOWN

    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown or expired handle"
        )
    if int(data["user_id"]) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Handle belongs to another user",
        )

    nc = AsyncNextcloud(nextcloud_url=nc_url())
    try:
        # timeout=1, step=1 makes exactly one HTTP attempt. The library default of 1200
        # would pin this worker for twenty minutes waiting on the user.
        creds = await nc.loginflow_v2.poll(
            data["poll_token"], timeout=1, step=1, overwrite_auth=False
        )
    except Exception:
        # Nextcloud answers 404 until the user approves, which nc-py-api raises.
        return NcLinkPoll(status="pending")

    now = datetime.now(timezone.utc)
    existing = (
        (
            await session.execute(
                select(NextcloudAccount).where(
                    NextcloudAccount.user_id == current_user.id
                )
            )
        )
        .scalars()
        .first()
    )
    if existing is None:
        existing = NextcloudAccount(user_id=current_user.id)
        session.add(existing)

    existing.nc_username = creds.login_name
    existing.app_password_enc = encrypt_secret(creds.app_password)
    existing.linked_at = now
    existing.checked_at = now
    await session.commit()

    try:
        await get_redis().delete(f"{HANDLE_PREFIX}{handle}")
    except RedisError:
        pass  # the handle expires on its own

    log.info(
        "Linked user %s to Nextcloud account %s", current_user.id, creds.login_name
    )
    return NcLinkPoll(status="linked", nc_username=creds.login_name)


@router.get("", response_model=NcLinkStatus, summary="Nextcloud link status")
async def link_status(current_user: User = Depends(get_current_user)):
    account = current_user.nc_account
    if account is None or not account.app_password_enc:
        return NcLinkStatus(linked=False)
    return NcLinkStatus(
        linked=True,
        nc_username=account.nc_username,
        linked_at=account.linked_at,
    )


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unlink the Nextcloud account",
)
async def unlink(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Forget the stored app password and fall back to the derived one.

    Nextcloud offers no API to revoke an app password, so the old one stays valid until the
    user removes it under Settings -> Security in Nextcloud itself.
    """
    account = (
        (
            await session.execute(
                select(NextcloudAccount).where(
                    NextcloudAccount.user_id == current_user.id
                )
            )
        )
        .scalars()
        .first()
    )
    if account is not None:
        await session.delete(account)
        await session.commit()
