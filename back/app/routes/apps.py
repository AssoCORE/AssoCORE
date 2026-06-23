"""
Nextcloud embedded-app URL routes.

These routes return the Nextcloud URL for a given app/view so the frontend
can open it in an iframe or redirect to it. They do not proxy data — use
/api/storage/* for file CRUD operations.
"""

import os

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.db.models import User

router = APIRouter(prefix="/apps", tags=["apps"])


def _nc_url() -> str:
    return os.getenv("NEXTCLOUD_URL", "http://localhost:8081").rstrip("/")


# ---------------------------------------------------------------------------
# Cloud file explorer
# ---------------------------------------------------------------------------


@router.get("/cloud", summary="Nextcloud Files app URL (root)")
async def cloud_root(current_user: User = Depends(get_current_user)):
    return {"url": f"{_nc_url()}/apps/files"}


@router.get("/cloud/folder", summary="Nextcloud Files app URL for a specific directory")
async def cloud_folder(
    dir: str = "",
    current_user: User = Depends(get_current_user),
):
    url = f"{_nc_url()}/apps/files"
    if dir:
        url += f"?dir={dir}"
    return {"url": url}


@router.get("/cloud/file", summary="Nextcloud Files app URL for a specific file")
async def cloud_file(
    dir: str = "",
    file: str = "",
    current_user: User = Depends(get_current_user),
):
    url = f"{_nc_url()}/apps/files"
    params = []
    if dir:
        params.append(f"dir={dir}")
    if file:
        params.append(f"openfile={file}")
    if params:
        url += "?" + "&".join(params)
    return {"url": url}


@router.get("/cloud/search", summary="Nextcloud Files search URL")
async def cloud_search(
    q: str = "",
    current_user: User = Depends(get_current_user),
):
    url = f"{_nc_url()}/apps/files"
    if q:
        url += f"?fileid=&query={q}"
    return {"url": url}


# ---------------------------------------------------------------------------
# File viewer (PDF / Office)
# ---------------------------------------------------------------------------


@router.get("/viewer", summary="Nextcloud file viewer URL by file ID")
async def file_viewer(
    file_id: str,
    current_user: User = Depends(get_current_user),
):
    return {"url": f"{_nc_url()}/apps/viewer?fileId={file_id}"}


# ---------------------------------------------------------------------------
# Calendar
# ---------------------------------------------------------------------------


@router.get("/calendar", summary="Nextcloud Calendar app URL")
async def calendar(current_user: User = Depends(get_current_user)):
    return {"url": f"{_nc_url()}/apps/calendar"}


@router.get(
    "/calendar/{view_type}", summary="Nextcloud Calendar app URL with a specific view"
)
async def calendar_view(
    view_type: str,
    current_user: User = Depends(get_current_user),
):
    return {"url": f"{_nc_url()}/apps/calendar/view/{view_type}"}


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


@router.get("/contacts", summary="Nextcloud Contacts app URL")
async def contacts(current_user: User = Depends(get_current_user)):
    return {"url": f"{_nc_url()}/apps/contacts"}


@router.get(
    "/contacts/{contact_id}",
    summary="Nextcloud Contacts app URL for a specific contact",
)
async def contact_detail(
    contact_id: str,
    current_user: User = Depends(get_current_user),
):
    return {"url": f"{_nc_url()}/apps/contacts/{contact_id}"}


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


@router.get("/notes", summary="Nextcloud Notes app URL")
async def notes(current_user: User = Depends(get_current_user)):
    return {"url": f"{_nc_url()}/apps/notes"}


@router.get("/notes/{note_id}", summary="Nextcloud Notes app URL for a specific note")
async def note_detail(
    note_id: str,
    current_user: User = Depends(get_current_user),
):
    return {"url": f"{_nc_url()}/apps/notes/{note_id}"}
