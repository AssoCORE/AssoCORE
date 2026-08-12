import asyncio
import io
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from nc_py_api import Nextcloud
from nc_py_api._exceptions import NextcloudException
from nc_py_api.files import FsNode

from app.core.crypto import decrypt_secret
from app.core.dependencies import get_current_user
from app.core.nextcloud import get_user_nc, nc_exception_to_http
from app.db.models import User
from app.schemas.classes import CopyRequest, FileNode, FolderCreate, MoveRequest

router = APIRouter(prefix="/storage", tags=["storage"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _nc(user: User) -> Nextcloud:
    """Nextcloud client acting as `user`.

    Prefers the app password from a linked account; a decrypt failure (rotated key) degrades
    to the derived password rather than failing the request.
    """
    account = user.nc_account
    if account is not None and account.app_password_enc:
        app_password = decrypt_secret(account.app_password_enc)
        if app_password:
            return get_user_nc(account.nc_username or user.username, app_password)
    return get_user_nc(user.username)


def _node_to_schema(node: FsNode) -> FileNode:
    last_mod = node.info.last_modified
    if not isinstance(last_mod, datetime):
        last_mod = datetime(1970, 1, 1)
    return FileNode(
        name=node.name,
        path=node.user_path,
        is_dir=node.is_dir,
        size=node.info.size,
        mime_type=node.info.mimetype,
        last_modified=last_mod,
        etag=node.etag,
        file_id=node.file_id,
    )


async def _run(func, *args, **kwargs):
    """Run a synchronous nc-py-api call in a thread pool."""
    try:
        return await asyncio.to_thread(func, *args, **kwargs)
    except NextcloudException as e:
        raise nc_exception_to_http(e)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
        )


# ---------------------------------------------------------------------------
# List / stat
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[FileNode],
    summary="List files and folders at the given path (default: root)",
)
async def list_files(
    path: str = Query(default="", description="Directory path relative to user root"),
    depth: int = Query(
        default=1, ge=1, le=5, description="How many directory levels to include"
    ),
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    nodes: list[FsNode] = await _run(nc.files.listdir, path, depth)
    return [_node_to_schema(n) for n in nodes]


@router.get(
    "/info",
    response_model=FileNode,
    summary="Get metadata for a specific file or folder",
)
async def get_info(
    path: str = Query(..., description="Path relative to user root"),
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    node: FsNode | None = await _run(nc.files.by_path, path)
    if node is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File or folder not found"
        )
    return _node_to_schema(node)


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=list[FileNode],
    summary="Search for files by name (supports * wildcard)",
)
async def search_files(
    q: str = Query(
        ..., min_length=1, description="Search term — use * as wildcard, e.g. '*.pdf'"
    ),
    path: str = Query(default="", description="Directory to search in (default: root)"),
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    pattern = q if "%" in q else f"%{q}%"
    nodes: list[FsNode] = await _run(nc.files.find, ["like", "name", pattern], path)
    return [_node_to_schema(n) for n in nodes]


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    response_model=FileNode,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a file",
)
async def upload_file(
    path: str = Query(
        ...,
        description="Destination path including filename, e.g. 'Documents/report.pdf'",
    ),
    file: UploadFile = File(...),
    overwrite: bool = Query(
        default=True, description="Overwrite if the file already exists"
    ),
    current_user: User = Depends(get_current_user),
):
    if not overwrite:
        nc = _nc(current_user)
        existing = await _run(nc.files.by_path, path)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="File already exists"
            )

    content = await file.read()
    nc = _nc(current_user)
    node: FsNode = await _run(nc.files.upload, path, content)
    return _node_to_schema(node)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


@router.get(
    "/download",
    summary="Download a file — returns raw binary content",
)
async def download_file(
    path: str = Query(..., description="File path relative to user root"),
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    content: bytes = await _run(nc.files.download, path)
    filename = path.rsplit("/", 1)[-1]
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Create folder
# ---------------------------------------------------------------------------


@router.post(
    "/folder",
    response_model=FileNode,
    status_code=status.HTTP_201_CREATED,
    summary="Create a folder (and all intermediate directories)",
)
async def create_folder(
    body: FolderCreate,
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    node: FsNode = await _run(nc.files.makedirs, body.path, True)
    if node is None:
        existing = await _run(nc.files.by_path, body.path)
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create folder",
            )
        return _node_to_schema(existing)
    return _node_to_schema(node)


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a file or folder (moves to trash if Nextcloud trash is enabled)",
)
async def delete(
    path: str = Query(..., description="Path relative to user root"),
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    await _run(nc.files.delete, path)


# ---------------------------------------------------------------------------
# Move / rename
# ---------------------------------------------------------------------------


@router.post(
    "/move",
    response_model=FileNode,
    summary="Move or rename a file or folder",
)
async def move(
    body: MoveRequest,
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    node: FsNode = await _run(nc.files.move, body.src, body.dst, body.overwrite)
    return _node_to_schema(node)


# ---------------------------------------------------------------------------
# Copy
# ---------------------------------------------------------------------------


@router.post(
    "/copy",
    response_model=FileNode,
    summary="Copy a file or folder",
)
async def copy(
    body: CopyRequest,
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    node: FsNode = await _run(nc.files.copy, body.src, body.dst, body.overwrite)
    return _node_to_schema(node)


# ---------------------------------------------------------------------------
# Favourites
# ---------------------------------------------------------------------------


@router.post(
    "/favourite",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark a file or folder as favourite",
)
async def set_favourite(
    path: str = Query(...),
    value: bool = Query(default=True),
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    await _run(nc.files.setfav, path, value)


@router.get(
    "/favourites",
    response_model=list[FileNode],
    summary="List all files and folders marked as favourite",
)
async def list_favourites(
    current_user: User = Depends(get_current_user),
):
    nc = _nc(current_user)
    nodes: list[FsNode] = await _run(nc.files.list_by_criteria, ["favorite"])
    return [_node_to_schema(n) for n in nodes]
