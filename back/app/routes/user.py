from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/user", tags=["user"])

# USER
@router.get("/login", description="login function")
async def login():
    return JSONResponse(content={"Response":"OK"})

@router.post("/create", description="create user")
async def create_user():
    return JSONResponse(content={"Response":"OK"})

@router.put("/update", description="update user")
async def update_user():
    return JSONResponse(content={"Response":"OK"})

@router.delete("/delete", description="delete user")
async def delete_user():
    return JSONResponse(content={"Response":"OK"})

@router.get("/{user_id}", description="get an user")
async def get_user(user_id):
    return JSONResponse(content={"Response":"OK"})

@router.get("/", description="get an user")
async def get_all_user(user_id):
    return JSONResponse(content={"Response":"OK"})



# NOTIFICATIONS
@router.get("/notification", description="get every notification")
async def get_notifications():
    return JSONResponse(content={"Response":"OK"})

@router.delete("/notification/{notification_id}", description="delete a specific notification")
async def delete_notification(notification_id):
    return JSONResponse(content={"Response":"OK"})

@router.put("/notification/{notification_id}", description="read/unread a specific notification")
async def change_status_notification(notification_id):
    return JSONResponse(content={"Response":"OK"})


@router.get("/notification/{notification_id}", description="get specific notification")
async def get_notification(notification_id):
    return JSONResponse(content={"Response":"OK"})


# REMINDERS
@router.post("/reminder", description="create new reminder for user")
async def create_reminder():
    return JSONResponse(content={"Response":"OK"})

@router.get("/reminder/{reminder_id}", description="get a specific reminder")
async def get_reminder(reminder_id):
    return JSONResponse(content={"Response":"OK"})

@router.delete("/reminder/{reminder_id}", description="delete a specific reminder")
async def delete_reminder(reminder_id):
    return JSONResponse(content={"Response":"OK"})

@router.get("/reminder/", description="get every reminder")
async def get_every_reminder():
    return JSONResponse(content={"Response":"OK"})

@router.delete("/reminder/", description="delete every reminder")
async def delete_reminder():
    return JSONResponse(content={"Response":"OK"})
