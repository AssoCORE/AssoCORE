import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from jwt import InvalidTokenError

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")
ALGORITHM = "HS256"

# Access tokens are short-lived because they are stateless: revoking one costs a redis entry
# that lives until it would have expired anyway. Long-lived sessions ride on refresh tokens.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

ACCESS = "access"
REFRESH = "refresh"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


@dataclass
class IssuedToken:
    token: str
    jti: str
    expires_at: datetime
    family: str | None = None


def _encode(
    user_id: int, token_type: str, expires_at: datetime, **extra
) -> IssuedToken:
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(user_id),
        "typ": token_type,
        "jti": jti,
        "iat": datetime.now(timezone.utc),
        "exp": expires_at,
        **extra,
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return IssuedToken(
        token=token, jti=jti, expires_at=expires_at, family=extra.get("fam")
    )


def create_access_token(user_id: int) -> IssuedToken:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return _encode(user_id, ACCESS, expires_at)


def create_refresh_token(
    user_id: int, family: str | None = None, expires_at: datetime | None = None
) -> IssuedToken:
    """Mint a refresh token.

    `expires_at` is passed on rotation so a rotated token inherits its predecessor's expiry —
    refreshing extends nothing, which makes REFRESH_TOKEN_EXPIRE_DAYS a true absolute session
    lifetime rather than a sliding window that never ends.
    """
    if expires_at is None:
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
    return _encode(user_id, REFRESH, expires_at, fam=family or uuid.uuid4().hex)


def create_token_pair(user_id: int) -> tuple[IssuedToken, IssuedToken]:
    return create_access_token(user_id), create_refresh_token(user_id)


def decode_token(token: str, expected_type: str = ACCESS) -> dict:
    """Decode and validate a token, returning its payload.

    Rejecting a mismatched `typ` is load-bearing: without it a refresh token would be a valid
    bearer credential on every protected route, which would defeat the short access TTL.
    Tokens issued before this scheme (no `typ`/`jti`) are rejected as invalid.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("typ") != expected_type:
        raise InvalidTokenError("Unexpected token type")
    if not payload.get("jti"):
        raise InvalidTokenError("Missing token id")
    return payload
