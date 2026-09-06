import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .core import redis_client
from .core.rate_limit import limiter
from .db import init_db
from .db.database import get_session
from .db.seed import seed_all
from .routes import api_router

log = logging.getLogger("assocore.access")


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    await seed_all()
    await redis_client.ping()
    yield
    await redis_client.close()


app = FastAPI(docs_url="/docs", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    ms = (time.perf_counter() - start) * 1000
    log.info(
        "%s %s %d %.1fms", request.method, request.url.path, response.status_code, ms
    )
    return response


@app.get("/")
def read_root():
    return {"message": "AssoCORE API"}


@app.get("/health", tags=["health"], summary="Liveness probe")
def health():
    """Deliberately static — the Kubernetes liveness probe points here.

    Checking the database would restart otherwise-healthy pods during a DB blip.
    """
    return {"status": "ok"}


@app.get("/ready", tags=["health"], summary="Readiness probe — checks DB and redis")
async def ready():
    errors = {}

    async for session in get_session():
        try:
            await session.execute(text("SELECT 1"))
        except Exception as e:
            errors["db"] = str(e)

    try:
        await redis_client.get_redis().ping()
    except Exception as e:
        errors["redis"] = str(e)

    if errors:
        return JSONResponse(
            status_code=503, content={"status": "degraded", "errors": errors}
        )
    return {"status": "ok"}
