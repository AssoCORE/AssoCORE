import importlib
from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/user", tags=["user"])

# USER
@router.get("/login", description="login function")
async def login():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create", description="create user")
async def create_user():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/update", description="update user")
async def update_user():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete", description="delete user")
async def delete_user():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", description="get an user")
async def get_user(user_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", description="get an user")
async def get_all_user(user_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# NOTIFICATIONS
@router.get("/notification", description="get every notification")
async def get_notifications():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/notification/{notification_id}", description="delete a specific notification")
async def delete_notification(notification_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/notification/{notification_id}", description="read/unread a specific notification")
async def change_status_notification(notification_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notification/{notification_id}", description="get specific notification")
async def get_notification(notification_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# REMINDERS
@router.post("/reminder", description="create new reminder for user")
async def create_reminder():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reminder/{reminder_id}", description="get a specific reminder")
async def get_reminder(reminder_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reminder/{reminder_id}", description="delete a specific reminder")
async def delete_reminder(reminder_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reminder/", description="get every reminder")
async def get_every_reminder():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reminder/", description="delete every reminder")
async def delete_reminder():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CLOUD
@router.get("/cloud/", description="send an address toward NextCloud's file system")
async def get_ns_iframe():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
