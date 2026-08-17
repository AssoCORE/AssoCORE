"""
Shared test fixtures.

Strategy:
- One SQLite in-memory database for the entire test session (fast, no MariaDB needed).
- Tables created once; roles seeded once.  Tests use unique usernames so they never step on
  each other and no per-test teardown is required.
- fakeredis replaces redis so TokenStore rotation / revocation works without a real redis.
- Nextcloud calls are patched out so tests run fully offline.
"""

from unittest.mock import AsyncMock, patch

import pytest

import fakeredis
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.rate_limit import limiter
from app.core.tokens import TokenStore, _CONSUME_LUA, get_token_store
from app.db.database import Base, get_session
from app.db.models import Role
from app.main import app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = None
_session_factory = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _setup_db():
    global _engine, _session_factory
    _engine = create_async_engine(_TEST_DB_URL, echo=False)
    _session_factory = async_sessionmaker(
        _engine, expire_on_commit=False, class_=AsyncSession
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with _session_factory() as s:
        s.add_all([Role(name="member"), Role(name="admin"), Role(name="staff")])
        await s.commit()
    yield
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session():
    async with _session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    fake_redis = fakeredis.FakeAsyncRedis(decode_responses=True)

    async def _get_session():
        yield db_session

    def _get_store():
        store = object.__new__(TokenStore)
        store._redis = fake_redis
        store._consume = fake_redis.register_script(_CONSUME_LUA)
        return store

    app.dependency_overrides[get_session] = _get_session
    app.dependency_overrides[get_token_store] = _get_store

    with (
        patch("app.routes.user.provision_nc_user", return_value=None),
        patch("app.routes.user._delete_nc_user", new_callable=AsyncMock),
        patch("app.routes.user._sync_nc_account", new_callable=AsyncMock),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _disable_rate_limiter():
    """Turn off rate limiting for every test — not under test here, and 5/min trips fast."""
    limiter.enabled = False
    yield
    limiter.enabled = True
