from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core import redis_client
from .core.rate_limit import limiter
from .db import init_db
from .db.seed import seed_all
from .routes import api_router


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


@app.get("/")
def read_root():
    return {"message": "AssoCORE API"}


@app.get("/health", tags=["health"], summary="Liveness probe")
def health():
    """Deliberately static — the Kubernetes liveness probe points here.

    Checking the database would restart otherwise-healthy pods during a DB blip.
    """
    return {"status": "ok"}
