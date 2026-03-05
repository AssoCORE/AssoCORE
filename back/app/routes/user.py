from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/user", tags=["user"])

# USER
@router.get("/login", description="login function")
async def login():
    return JSONResponse(content={"OK"})

@router.post("/create", description="create user")
async def create_user():
    return JSONResponse(content={"OK"})

@router.put("/update", description="update user")
async def update_user():
    return JSONResponse(content={"OK"})

@router.delete("/delete", description="delete user")
async def delete_user():
    return JSONResponse(content={"OK"})

@router.get("/{user_id}", description="get an user")
async def get_user(user_id):
    return JSONResponse(content={"OK"})

@router.get("/", description="get an user")
async def get_all_user(user_id):
    return JSONResponse(content={"OK"})



# NOTIFICATIONS
@router.post("/notification", description="send a new notification to all targets")
async def create_get_notification():
    return JSONResponse(content={"OK"})

@router.get("/notification", description="send a new notification to all targets")
async def get_notification():
    return JSONResponse(content={"OK"})

@router.delete("/notification", description="send a new notification to all targets")
async def delete_notification():
    return JSONResponse(content={"OK"})

@router.post("/{user_id}/notification", description="create new notification")
async def create_notification(user_id: str):
    return JSONResponse(content={"OK"})

@router.get("/notifications", description="get user notifications")
async def get_notifications():
    return JSONResponse(content={"OK"})


# REMINDERS
@router.post("/reminder", description="create new reminder for user")
async def create_reminder():
    return JSONResponse(content={"OK"})

@router.get("/reminder/{reminder_id}", description="get a specific reminder")
async def get_reminder(reminder_id):
    return JSONResponse(content={"OK"})

@router.delete("/reminder/{reminder_id}", description="delete a specific reminder")
async def delete_reminder(reminder_id):
    return JSONResponse(content={"OK"})

@router.get("/reminder/", description="get every reminder")
async def get_reminder():
    return JSONResponse(content={"OK"})

@router.delete("/reminder/", description="delete every reminder")
async def delete_reminder():
    return JSONResponse(content={"OK"})
