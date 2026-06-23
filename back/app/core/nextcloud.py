import hashlib
import hmac
import os

from fastapi import HTTPException, status
from nc_py_api import Nextcloud
from nc_py_api._exceptions import NextcloudException


def derive_nc_password(username: str) -> str:
    """Deterministic per-user Nextcloud password derived from SECRET_KEY + username."""
    key = os.getenv("SECRET_KEY", "change-me-in-production").encode()
    return hmac.new(key, username.encode(), hashlib.sha256).hexdigest()


def get_admin_nc() -> Nextcloud:
    return Nextcloud(
        nextcloud_url=os.getenv("NEXTCLOUD_URL", "http://nextcloud"),
        nc_auth_user=os.getenv("NEXTCLOUD_USER", "admin"),
        nc_auth_pass=os.getenv("NEXTCLOUD_PASSWORD", "admin"),
    )


def get_user_nc(username: str) -> Nextcloud:
    return Nextcloud(
        nextcloud_url=os.getenv("NEXTCLOUD_URL", "http://nextcloud"),
        nc_auth_user=username,
        nc_auth_pass=derive_nc_password(username),
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
