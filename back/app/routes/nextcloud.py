import importlib
import os
from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/nextcloud", tags=["nextcloud"])


def get_nc_client() -> Any:
    try:
        Nextcloud = importlib.import_module("nc_py_api").Nextcloud
    except ImportError as exc:
        raise HTTPException(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            detail="Nextcloud integration unavailable: missing nc_py_api dependency",
        ) from exc

    return Nextcloud(
        nextcloud_url=os.getenv("NEXTCLOUD_URL", "http://nextcloud"),
        nc_auth_user=os.getenv("NEXTCLOUD_USER", "admin"),
        nc_auth_pass=os.getenv("NEXTCLOUD_PASSWORD", "admin"),
    )


@router.get("/users", description="Get all Nextcloud users")
async def get_nextcloud_users():
    try:
        nc = get_nc_client()
        users = nc.users.get_list()
        return JSONResponse(content={"users": users})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{user_id}", description="Get files for a Nextcloud user")
async def get_user_files(user_id: str):
    try:
        nc = get_nc_client()
        files = nc.files.listdir(f"/{user_id}/files")
        return JSONResponse(content={"files": [f.name for f in files]})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class NextcloudCreateUserModel(BaseModel):
    username: str
    password: str
    email: Optional[str] = None


@router.post("/users", description="Create a new Nextcloud user")
async def create_nextcloud_user(user: NextcloudCreateUserModel):
    try:
        nc = get_nc_client()
        users_api = getattr(nc, "users", None)
        if users_api is None:
            raise RuntimeError("Nextcloud client has no `users` API")

        method_names = ["create", "add", "create_user", "add_user", "createUser"]
        last_exc = None
        for name in method_names:
            if hasattr(users_api, name):
                func = getattr(users_api, name)
                try:
                    kwargs = {"user_id": user.username, "password": user.password}
                    if user.email:
                        kwargs["email"] = user.email
                    result = func(**kwargs)
                    return JSONResponse(
                        status_code=HTTPStatus.CREATED, content={"result": result}
                    )
                except TypeError:
                    try:
                        if user.email:
                            result = func(user.username, user.password, user.email)
                        else:
                            result = func(user.username, user.password)
                        return JSONResponse(
                            status_code=HTTPStatus.CREATED, content={"result": result}
                        )
                    except Exception as e:
                        last_exc = e
                        continue
                except Exception as e:
                    last_exc = e
                    continue

        raise RuntimeError(
            str(last_exc)
            if last_exc
            else "No supported user-creation method found on Nextcloud client"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
