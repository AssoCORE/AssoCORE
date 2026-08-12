import logging
import os

from redis.asyncio import Redis
from redis.exceptions import RedisError

log = logging.getLogger(__name__)

# Nextcloud uses redis DB 0 for its own cache. Auth state lives on a separate index so an
# `occ` cache flush on the Nextcloud side cannot log every user out.
REDIS_URL = os.getenv("REDIS_URL") or (
    f"redis://{os.getenv('REDIS_HOST', 'redis')}"
    f":{os.getenv('REDIS_PORT', '6379')}"
    f"/{os.getenv('REDIS_DB', '1')}"
)

_client: Redis | None = None


def get_redis() -> Redis:
    """Process-wide redis client.

    A redis-py client *is* a connection pool, so one instance per process is correct —
    building one per request would leak connections.
    """
    global _client
    if _client is None:
        _client = Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            # Without these a dead redis makes every authenticated request hang for the
            # OS TCP timeout instead of failing fast.
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
            health_check_interval=30,
        )
    return _client


async def ping() -> bool:
    """Probe redis at startup. Never raises — a missing redis degrades, it does not crash the API."""
    try:
        await get_redis().ping()
        return True
    except RedisError:
        log.warning("Redis unreachable at %s — auth revocation will degrade", REDIS_URL)
        return False


async def close() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
