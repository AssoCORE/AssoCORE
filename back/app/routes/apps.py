import importlib
from http import HTTPStatus
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter(prefix="/apps", tags=["apps"])


# CLOUD
@router.get("/cloud/", description="send an address toward NextCloud's file system")
async def get_ns_cloud():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cloud/?dir={dir}", description="send an address toward NextCloud's file system")
async def get_ns_specific_folder(dir):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cloud/?dir={dir}&file={file}", description="send an address towards specific file into Nextcloud")
async def get_ns__specific_file(dir, file):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cloud/search/{filename}", description="send an address towards Nextcloud's search file system")
async def get_ns__specific_file(dir, file):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# FILE VIEWER
@router.get("/file/{id}", description="send an address toward Nextcloud's file viewer")
async def get_ns_file_viewer(id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CALENDAR
@router.get("/calendar/", description="send an address toward NextCloud's calendar system")
async def get_ns_calendar():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/view={viewType}", description="send an address toward NextCloud's calendar system with specific view type")
async def get_ns_specific_calendar(viewType):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# CONTACTS
@router.get("/contact/", description="send an address toward NextCloud's contact system")
async def get_ns_contacts():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contact/{contact_id}", description="send an address toward NextCloud's contact system with a specific target")
async def get_ns_specific_contacts(contact_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOTES
@router.get("/notes/", description="send an address toward NextCloud's notes system")
async def get_ns_notes():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notes/{note_id}", description="send an address toward NextCloud's notes system with a specific target")
async def get_ns_specific_note(note_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
