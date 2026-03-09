from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/event", tags=["event"])

@router.get("/{event_id}", description="get all event")
async def get_event(event_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", description="get a event")
async def get_all_event():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", description="create a new event")
async def post_event():
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{event_id}", description="modify an event")
async def modify_event(event_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{event_id}", description="remove an event")
async def remove_event(event_id):
    try:
        return JSONResponse(content={"Response":"OK"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

