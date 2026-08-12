import hashlib
import hmac
import os

from fastapi import HTTPException, status
from nc_py_api import AsyncNextcloud, Nextcloud
from nc_py_api._exceptions import NextcloudException


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
