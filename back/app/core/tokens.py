"""Redis-backed storage for token revocation and refresh-token rotation.

Access tokens stay stateless and short-lived; only their `jti` is blacklisted, with a TTL
equal to the token's remaining life, so the blacklist can never grow past the set of
unexpired tokens and needs no cleanup job.

Refresh tokens are stored server-side and rotated on every use, with reuse detection: a
replay outside the grace window kills the whole token family (all tokens descended from one
login), which is the standard OAuth 2.1 response to a stolen refresh token.
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from redis.exceptions import RedisError

from app.core.redis_client import get_redis

log = logging.getLogger(__name__)

PREFIX = "assocore:auth:"

# How long a just-consumed refresh token keeps answering with its replacement pair.
# Without this, two browser tabs refreshing at the same moment would look like token theft
# and the second one would kill the family, logging out a legitimate user.
REFRESH_GRACE_SECONDS = int(os.getenv("REFRESH_GRACE_SECONDS", "10"))

# When false (the default) a redis outage lets access tokens through unvalidated rather than
# taking the whole API down; the short access TTL bounds the exposure. Set true in prod to
# fail closed instead.
AUTH_REDIS_STRICT = os.getenv("AUTH_REDIS_STRICT", "false").lower() in (
    "1",
    "true",
    "yes",
)


class RedisUnavailable(Exception):
    """Redis could not be reached for an operation that must not silently succeed."""


def _access_key(jti: str) -> str:
    return f"{PREFIX}access:revoked:{jti}"


def _refresh_key(jti: str) -> str:
    return f"{PREFIX}refresh:{jti}"


def _family_key(family: str) -> str:
    return f"{PREFIX}family:{family}"


def _family_dead_key(family: str) -> str:
    return f"{PREFIX}family:dead:{family}"


def _user_families_key(user_id: int) -> str:
    return f"{PREFIX}user:{user_id}:families"


def _ttl_from(expires_at: datetime) -> int:
    remaining = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return max(remaining, 1)


# Atomically move a refresh token through active -> consumed, so that concurrent callers get
# a coherent answer. Doing this as GET + DEL in Python would let two racing requests both
# believe they consumed the token.
_CONSUME_LUA = """
local state = redis.call('HGET', KEYS[1], 'state')
if state == false then
  return {'REUSE'}
end
if state == 'active' then
  redis.call('HSET', KEYS[1], 'state', 'consumed', 'consumed_at', ARGV[1])
  redis.call('EXPIRE', KEYS[1], ARGV[2])
  local d = redis.call('HMGET', KEYS[1], 'user_id', 'fam', 'exp')
  return {'OK', d[1], d[2], d[3]}
end
if state == 'consumed' then
  local consumed_at = tonumber(redis.call('HGET', KEYS[1], 'consumed_at'))
  if consumed_at and (tonumber(ARGV[1]) - consumed_at) <= tonumber(ARGV[2]) then
    local d = redis.call('HMGET', KEYS[1], 'next_access', 'next_refresh')
    if d[1] and d[2] then
      return {'GRACE', d[1], d[2]}
    end
    return {'PENDING'}
  end
end
return {'REUSE'}
"""


@dataclass
class ConsumeResult:
    """Outcome of trying to spend a refresh token.

    status is one of:
      OK      -- consumed; issue a new pair inheriting `exp`
      GRACE   -- a racing request already consumed it; replay its replacement pair verbatim
      PENDING -- consumed microseconds ago, replacement not stored yet; the client should retry
      REUSE   -- unknown or long-consumed token; treat as theft and kill the family
    """

    status: str
    user_id: int | None = None
    family: str | None = None
    expires_at: datetime | None = None
    next_access: str | None = None
    next_refresh: str | None = None


class TokenStore:
    def __init__(self) -> None:
        self._redis = get_redis()
        self._consume = self._redis.register_script(_CONSUME_LUA)

    # -- access tokens ----------------------------------------------------

    async def revoke_access(self, jti: str, expires_at: datetime) -> None:
        try:
            await self._redis.set(_access_key(jti), "1", ex=_ttl_from(expires_at))
        except RedisError as e:
            raise RedisUnavailable(str(e)) from e

    async def is_access_revoked(self, jti: str) -> bool:
        try:
            return await self._redis.exists(_access_key(jti)) == 1
        except RedisError as e:
            if AUTH_REDIS_STRICT:
                raise RedisUnavailable(str(e)) from e
            log.warning("Redis down — skipping revocation check for jti %s", jti)
            return False

    # -- refresh tokens ---------------------------------------------------

    async def store_refresh(
        self, jti: str, user_id: int, family: str, expires_at: datetime
    ) -> None:
        ttl = _ttl_from(expires_at)
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                pipe.hset(
                    _refresh_key(jti),
                    mapping={
                        "user_id": str(user_id),
                        "fam": family,
                        "exp": expires_at.isoformat(),
                        "state": "active",
                    },
                )
                pipe.expire(_refresh_key(jti), ttl)
                pipe.sadd(_family_key(family), jti)
                # Outlive the tokens themselves so reuse detection can still enumerate them.
                pipe.expire(_family_key(family), ttl + 60)
                # Track all families per user so logout/all can kill them in one call.
                pipe.sadd(_user_families_key(user_id), family)
                pipe.expire(_user_families_key(user_id), ttl + 3600)
                await pipe.execute()
        except RedisError as e:
            raise RedisUnavailable(str(e)) from e

    async def consume_refresh(self, jti: str) -> ConsumeResult:
        try:
            raw = await self._consume(
                keys=[_refresh_key(jti)],
                args=[str(int(time.time())), str(REFRESH_GRACE_SECONDS)],
            )
        except RedisError as e:
            raise RedisUnavailable(str(e)) from e

        status = raw[0]
        if status == "OK":
            return ConsumeResult(
                status="OK",
                user_id=int(raw[1]),
                family=raw[2],
                expires_at=datetime.fromisoformat(raw[3]),
            )
        if status == "GRACE":
            return ConsumeResult(
                status="GRACE", next_access=raw[1], next_refresh=raw[2]
            )
        return ConsumeResult(status=status)

    async def cache_replacement(self, jti: str, access: str, refresh: str) -> None:
        """Record the pair issued in exchange for `jti`, so a racing replay gets the same answer."""
        try:
            await self._redis.hset(
                _refresh_key(jti),
                mapping={"next_access": access, "next_refresh": refresh},
            )
        except RedisError as e:
            raise RedisUnavailable(str(e)) from e

    # -- families ---------------------------------------------------------

    async def is_family_dead(self, family: str) -> bool:
        try:
            return await self._redis.exists(_family_dead_key(family)) == 1
        except RedisError as e:
            raise RedisUnavailable(str(e)) from e

    async def kill_family(self, family: str, ttl: int) -> None:
        """Revoke every refresh token descended from one login and tombstone the family."""
        try:
            members = await self._redis.smembers(_family_key(family))
            async with self._redis.pipeline(transaction=True) as pipe:
                for member in members:
                    pipe.delete(_refresh_key(member))
                pipe.delete(_family_key(family))
                pipe.set(_family_dead_key(family), "1", ex=max(ttl, 1))
                await pipe.execute()
        except RedisError as e:
            raise RedisUnavailable(str(e)) from e

    async def kill_user_sessions(self, user_id: int, refresh_ttl: int) -> None:
        """Revoke all active refresh token families for a user (logout everywhere)."""
        key = _user_families_key(user_id)
        try:
            families = await self._redis.smembers(key)
            for family in families:
                await self.kill_family(family, refresh_ttl)
            await self._redis.delete(key)
        except RedisError as e:
            raise RedisUnavailable(str(e)) from e


def get_token_store() -> TokenStore:
    return TokenStore()
