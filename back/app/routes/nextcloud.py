import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import get_current_user
from app.core.nextcloud import get_admin_nc, nc_exception_to_http
from app.db.models import User

router = APIRouter(prefix="/nextcloud", tags=["nextcloud (admin)"])


async def _run(func, *args, **kwargs):
    try:
        return await asyncio.to_thread(func, *args, **kwargs)
    except Exception as e:
        raise nc_exception_to_http(e)


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@router.get("/users", summary="List all Nextcloud users (admin)")
async def get_users(_: User = Depends(get_current_user)):
    nc = get_admin_nc()
    users = await _run(nc.users.get_list)
    return {"users": users}


class CreateNcUserBody(BaseModel):
    username: str
    password: str
    email: str | None = None
    display_name: str | None = None


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    summary="Create a Nextcloud user (admin)",
)
async def create_user(body: CreateNcUserBody, _: User = Depends(get_current_user)):
    nc = get_admin_nc()
    await _run(
        nc.users.create,
        body.username,
        password=body.password,
        email=body.email or "",
        display_name=body.display_name or body.username,
    )
    return {"username": body.username}


@router.delete(
    "/users/{username}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Nextcloud user (admin)",
)
async def delete_nc_user(username: str, _: User = Depends(get_current_user)):
    nc = get_admin_nc()
    await _run(nc.users.delete, username)


@router.put(
    "/users/{username}/enable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Enable a Nextcloud user",
)
async def enable_nc_user(username: str, _: User = Depends(get_current_user)):
    nc = get_admin_nc()
    await _run(nc.users.enable, username)


@router.put(
    "/users/{username}/disable",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Disable a Nextcloud user",
)
async def disable_nc_user(username: str, _: User = Depends(get_current_user)):
    nc = get_admin_nc()
    await _run(nc.users.disable, username)


# ---------------------------------------------------------------------------
# Files (admin — access any user's storage)
# ---------------------------------------------------------------------------


@router.get("/files/{username}", summary="List files for a specific user (admin)")
async def get_user_files(
    username: str, path: str = "", _: User = Depends(get_current_user)
):
    nc = get_admin_nc()
    try:
        files = await _run(nc.files.listdir, f"/{username}/files/{path.lstrip('/')}")
    except HTTPException:
        raise
    except Exception as e:
        raise nc_exception_to_http(e)
    return {
        "files": [
            {"name": f.name, "is_dir": f.is_dir, "size": f.info.size} for f in files
        ]
    }
