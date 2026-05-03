import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from nc_py_api import Nextcloud

from app.db.database import get_session
from app.db.models import User

router = APIRouter(prefix="/user", tags=["user"])

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-secure-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login", description="Login via Nextcloud credentials")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    # 1. Verify credentials against Nextcloud
    try:
        nc_url = os.getenv("NEXTCLOUD_URL", "http://nextcloud")
        # We initialize the Nextcloud client using the credentials the user just typed in
        nc = Nextcloud(
            nextcloud_url=nc_url,
            nc_auth_user=form_data.username,
            nc_auth_pass=form_data.password,
        )

        # Make a lightweight API call to verify the credentials work
        import nc_py_api

        try:
            nc_user = (
                nc.users.get_user()
            )  # no arg = current user, no admin rights needed
        except nc_py_api.NextcloudException:
            raise ValueError("Invalid Nextcloud credentials")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Check if the user exists in your local MariaDB
    result = await session.execute(
        select(User).where(User.username == form_data.username)
    )
    local_user = result.scalars().first()

    # (Optional) If the user exists in Nextcloud but not locally, you could auto-create them here.
    if not local_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User authenticated in Nextcloud but has no local AssoCORE profile.",
        )

    # 3. Generate the local JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )

    # Return standard OAuth2 token response
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/create", description="create user")
async def create_user():
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update", description="update user")
async def update_user():
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{user_id}", description="delete user")
async def delete_user(user_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}", description="get an user")
async def get_user(user_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", description="get all user")
async def get_all_user():
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOTIFICATIONS
@router.get("/notification", description="get every notification")
async def get_notifications():
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete(
    "/notification/{notification_id}", description="delete a specific notification"
)
async def delete_notification(notification_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/notification/read/{notification_id}", description="read a specific notification"
)
async def read_notification(notification_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/notification/unread/{notification_id}",
    description="unread a specific notification",
)
async def unread_notification(notification_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notification/{notification_id}", description="get specific notification")
async def get_notification(notification_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# REMINDERS
@router.post("/reminder", description="create new reminder for user")
async def create_reminder():
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reminder/{reminder_id}", description="get a specific reminder")
async def get_reminder(reminder_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reminder/{reminder_id}", description="delete a specific reminder")
async def delete_reminder(reminder_id):
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reminder/", description="get every reminder")
async def get_every_reminder():
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/reminder/", description="delete every reminder")
async def delete_reminder():
    try:
        return JSONResponse(content={"Response": "OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
