import asyncio
import hashlib
import hmac
import logging
import os

from fastapi import HTTPException, status
from nc_py_api import AsyncNextcloud, Nextcloud
from nc_py_api._exceptions import NextcloudException

log = logging.getLogger(__name__)

# Bounds how long a login can wait on Nextcloud before giving up.
NC_PROBE_TIMEOUT = float(os.getenv("NC_PROBE_TIMEOUT", "3.0"))
# How long a successful probe is trusted before re-checking, so steady-state logins cost no
# Nextcloud round-trip at all.
NC_PROBE_INTERVAL_HOURS = int(os.getenv("NC_PROBE_INTERVAL_HOURS", "24"))
SELF_HEAL_ENABLED = os.getenv("NC_LOGIN_SELF_HEAL", "true").lower() in (
    "1",
    "true",
    "yes",
)


def nc_url() -> str:
    """Base URL the API uses to reach Nextcloud (container DNS in docker)."""
    return os.getenv("NEXTCLOUD_URL", "http://nextcloud")


def nc_public_url() -> str:
    """Base URL a *browser* can reach Nextcloud on.

    Distinct from `nc_url()`: the API talks to `http://nextcloud`, which resolves nowhere
    outside the docker network, so any URL handed to a user must be rewritten to this one.
    """
    return os.getenv("NEXTCLOUD_PUBLIC_URL", "http://localhost:8081")


def to_public_url(url: str) -> str:
    return url.replace(nc_url(), nc_public_url(), 1)


def derive_nc_password(username: str) -> str:
    """Deterministic per-user Nextcloud password derived from SECRET_KEY + username.

    Fallback for accounts that have not been linked via Login Flow v2. Note that a SECRET_KEY
    leak yields every user's Nextcloud password — linking a real app password is the upgrade.
    """
    key = os.getenv("SECRET_KEY", "change-me-in-production").encode()
    return hmac.new(key, username.encode(), hashlib.sha256).hexdigest()


def admin_credentials() -> tuple[str, str]:
    """Nextcloud admin credentials.

    ``NEXTCLOUD_ADMIN_USER`` / ``NEXTCLOUD_ADMIN_PASSWORD`` are the names used by .env,
    docker-compose and the Nextcloud image itself. The bare ``NEXTCLOUD_USER`` /
    ``NEXTCLOUD_PASSWORD`` names are kept as a fallback so existing local setups keep working.
    """
    user = os.getenv("NEXTCLOUD_ADMIN_USER") or os.getenv("NEXTCLOUD_USER") or "admin"
    password = (
        os.getenv("NEXTCLOUD_ADMIN_PASSWORD")
        or os.getenv("NEXTCLOUD_PASSWORD")
        or "admin"
    )
    return user, password


def get_admin_nc() -> Nextcloud:
    user, password = admin_credentials()
    return Nextcloud(nextcloud_url=nc_url(), nc_auth_user=user, nc_auth_pass=password)


def get_async_admin_nc() -> AsyncNextcloud:
    user, password = admin_credentials()
    return AsyncNextcloud(
        nextcloud_url=nc_url(), nc_auth_user=user, nc_auth_pass=password
    )


def get_user_nc(username: str, app_password: str | None = None) -> Nextcloud:
    """Client acting as `username`, using a linked app password when one is available."""
    return Nextcloud(
        nextcloud_url=nc_url(),
        nc_auth_user=username,
        nc_auth_pass=app_password or derive_nc_password(username),
    )


def get_async_user_nc(username: str, app_password: str | None = None) -> AsyncNextcloud:
    return AsyncNextcloud(
        nextcloud_url=nc_url(),
        nc_auth_user=username,
        nc_auth_pass=app_password or derive_nc_password(username),
    )


def provision_nc_user(username: str, email: str = "", display_name: str = "") -> None:
    """Create a Nextcloud account for an AssoCORE user. Safe to call multiple times (idempotent)."""
    nc = get_admin_nc()
    try:
        nc.users.create(
            username,
            password=derive_nc_password(username),
            email=email,
            display_name=display_name or username,
        )
    except NextcloudException as e:
        if e.status_code == 102:  # OCS: user already exists
            return
        raise


async def ensure_nc_account(
    username: str,
    email: str = "",
    display_name: str = "",
    app_password: str | None = None,
) -> bool:
    """Make sure `username` has a working Nextcloud account, provisioning it if not.

    Repairs accounts for users who registered while Nextcloud was down. Returns True when the
    account is usable.

    Uses AsyncNextcloud rather than a thread so `asyncio.wait_for` can genuinely bound how
    long a login waits on Nextcloud — cancelling a thread would leave its socket running.
    """
    user_nc = get_async_user_nc(username, app_password)
    if await asyncio.wait_for(user_nc.perform_login(), timeout=NC_PROBE_TIMEOUT):
        return True

    if app_password:
        # A linked account failing to authenticate most likely means the user rotated their
        # own Nextcloud password. Resetting it through the admin API would hijack a real
        # account, so stop here and let them re-link.
        log.warning(
            "Nextcloud rejected the linked app password for %s — leaving it untouched",
            username,
        )
        return False

    admin_nc = get_async_admin_nc()
    if not await asyncio.wait_for(admin_nc.perform_login(), timeout=NC_PROBE_TIMEOUT):
        # perform_login() returns False both for bad credentials and for an unreachable
        # server, so an admin failure here means Nextcloud is down, not that the user is
        # missing. Provisioning would be wrong either way.
        log.warning("Nextcloud unreachable — skipping account check for %s", username)
        return False

    try:
        await admin_nc.users.create(
            username,
            password=derive_nc_password(username),
            email=email,
            display_name=display_name or username,
        )
        log.info("Provisioned missing Nextcloud account for %s", username)
        return True
    except NextcloudException as e:
        if e.status_code != 102:  # anything but "already exists"
            raise
        # The account exists but rejected our password — the derived password drifted
        # (usually a SECRET_KEY change). Reset it back to what we can reproduce.
        await admin_nc.users.edit(username, password=derive_nc_password(username))
        log.info("Repaired the derived Nextcloud password for %s", username)
        return True


def nc_exception_to_http(e: Exception) -> HTTPException:
    """Convert a NextcloudException to a FastAPI HTTPException."""
    if isinstance(e, NextcloudException):
        if e.status_code == 404:
            return HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="File or folder not found"
            )
        if e.status_code == 403:
            return HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        if e.status_code == 409:
            return HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Already exists"
            )
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Nextcloud error: {e}"
        )
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Nextcloud unavailable"
    )
