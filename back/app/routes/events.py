from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/event", tags=["event"])

@router.get("/{event_id}", description="get all event")
async def get_event(event_id):
    pass

@router.get("/", description="get a event")
async def get_all_event():
    pass

@router.post("/", description="create a new event")
async def post_event():
    pass

@router.put("/{event_id}", description="modify an event")
async def modify_event(event_id):
    pass

@router.delete("/{event_id}", description="remove an event")
async def remove_event(event_id):
    pass
