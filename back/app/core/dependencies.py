from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.roles import ROLE_ADMIN
from app.core.security import decode_token
from app.core.tokens import RedisUnavailable, TokenStore, get_token_store
from app.db import get_session
from app.db.models import User

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    session: AsyncSession = Depends(get_session),
    store: TokenStore = Depends(get_token_store),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    try:
        if await store.is_access_revoked(payload["jti"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked"
            )
    except RedisUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication backend unavailable",
        )

    # Eager-load rather than session.get(): async SQLAlchemy cannot lazy-load, and both
    # require_roles (roles) and storage.py (nc_account) read these on every request.
    result = await session.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == int(payload["sub"]))
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )
    return user


def require_roles(*names: str):
    """Build a dependency that admits only users holding one of `names`.

    Relies on `get_current_user` eager-loading `roles` — async SQLAlchemy cannot lazy-load.
    """

    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        if not {role.name for role in current_user.roles} & set(names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role"
            )
        return current_user

    return _dep


require_admin = require_roles(ROLE_ADMIN)
