import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jwt import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import bearer, get_current_user
from app.core.nextcloud import provision_nc_user
from app.core.roles import ROLE_MEMBER
from app.core.security import (
    REFRESH,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.tokens import RedisUnavailable, TokenStore, get_token_store
from app.db.database import get_session
from app.db.models import Notification, Reminder, Role, User

log = logging.getLogger(__name__)
from app.schemas.classes import (
    LoginRequest,
    LogoutRequest,
    NotificationOut,
    RefreshRequest,
    ReminderCreate,
    ReminderOut,
    Token,
    UserCreate,
    UserOut,
    UserUpdate,
)

router = APIRouter(prefix="/user", tags=["user"])


def _user_q():
    return select(User).options(
        selectinload(User.roles),
        selectinload(User.notifications),
        selectinload(User.reminders),
    )


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
)
AUTH_BACKEND_DOWN = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail="Authentication backend unavailable",
)


def _expires_in(expires_at: datetime) -> int:
    return max(int((expires_at - datetime.now(timezone.utc)).total_seconds()), 0)


async def _issue_pair(
    user_id: int,
    store: TokenStore,
    family: str | None = None,
    refresh_expires_at: datetime | None = None,
) -> Token:
    access = create_access_token(user_id)
    refresh = create_refresh_token(
        user_id, family=family, expires_at=refresh_expires_at
    )
    await store.store_refresh(refresh.jti, user_id, refresh.family, refresh.expires_at)
    return Token(
        access_token=access.token,
        refresh_token=refresh.token,
        expires_in=_expires_in(access.expires_at),
    )


@router.post(
    "/login", response_model=Token, summary="Authenticate and get a token pair"
)
async def login(
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
    store: TokenStore = Depends(get_token_store),
):
    result = await session.execute(select(User).where(User.username == body.username))
    user = result.scalars().first()
    if not user or not verify_password(body.password, user.password):
        raise UNAUTHORIZED
    try:
        return await _issue_pair(user.id, store)
    except RedisUnavailable:
        raise AUTH_BACKEND_DOWN


@router.post(
    "/refresh", response_model=Token, summary="Exchange a refresh token for a new pair"
)
async def refresh(body: RefreshRequest, store: TokenStore = Depends(get_token_store)):
    """Rotate a refresh token.

    Takes no Authorization header — the access token is expected to have expired, which is
    the whole reason the client is here.
    """
    try:
        payload = decode_token(body.refresh_token, expected_type=REFRESH)
    except (ExpiredSignatureError, InvalidTokenError):
        raise UNAUTHORIZED

    jti = payload["jti"]
    family = payload.get("fam")
    if not family:
        raise UNAUTHORIZED

    try:
        if await store.is_family_dead(family):
            raise UNAUTHORIZED
        result = await store.consume_refresh(jti)

        if result.status == "GRACE":
            # A concurrent request already rotated this token; hand back the same pair so N
            # racing tabs converge on one session instead of tripping reuse detection.
            access_payload = decode_token(result.next_access)
            return Token(
                access_token=result.next_access,
                refresh_token=result.next_refresh,
                expires_in=_expires_in(
                    datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
                ),
            )

        if result.status == "PENDING":
            # Consumed microseconds ago by a request still in flight.
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Refresh in progress, retry",
                headers={"Retry-After": "1"},
            )

        if result.status != "OK":
            log.warning(
                "Refresh token reuse detected (family %s) — revoking the family", family
            )
            await store.kill_family(family, REFRESH_TOKEN_EXPIRE_DAYS * 86400)
            raise UNAUTHORIZED

        pair = await _issue_pair(
            result.user_id,
            store,
            family=result.family,
            refresh_expires_at=result.expires_at,
        )
        await store.cache_replacement(jti, pair.access_token, pair.refresh_token)
        return pair
    except RedisUnavailable:
        # The refresh token exists only in redis, so we cannot verify it. Fail closed.
        raise AUTH_BACKEND_DOWN


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the current access token and end the session",
)
async def logout(
    body: LogoutRequest | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    _: User = Depends(get_current_user),
    store: TokenStore = Depends(get_token_store),
):
    payload = decode_token(credentials.credentials)
    try:
        await store.revoke_access(
            payload["jti"], datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        )
        if body and body.refresh_token:
            try:
                refresh_payload = decode_token(
                    body.refresh_token, expected_type=REFRESH
                )
            except (ExpiredSignatureError, InvalidTokenError):
                return
            family = refresh_payload.get("fam")
            if family:
                # Kill the whole family, not just this token — that is what "log out" means.
                await store.kill_family(family, REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    except RedisUnavailable:
        # Reporting a successful logout when nothing was revoked would be a lie.
        raise AUTH_BACKEND_DOWN


# ---------------------------------------------------------------------------
# User CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def create_user(body: UserCreate, session: AsyncSession = Depends(get_session)):
    clash = await session.execute(
        select(User).where(
            (User.username == body.username) | (User.mail == str(body.mail))
        )
    )
    if clash.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already taken",
        )

    member = (
        (await session.execute(select(Role).where(Role.name == ROLE_MEMBER)))
        .scalars()
        .first()
    )

    user = User(
        name=body.name,
        firstname=body.firstname,
        username=body.username,
        password=hash_password(body.password),
        mail=str(body.mail),
        phone=body.phone,
        birth_date=body.birth_date,
        # Assigned before add() — on a transient object this initialises the collection
        # without a round-trip; appending after commit would lazy-load and blow up.
        roles=[member] if member else [],
    )
    session.add(user)
    await session.commit()

    # Provision a matching Nextcloud account (best-effort — does not block registration)
    try:
        await asyncio.to_thread(
            provision_nc_user,
            body.username,
            str(body.mail),
            f"{body.firstname} {body.name}",
        )
    except Exception:
        log.warning(
            "Failed to provision Nextcloud user for %s", body.username, exc_info=True
        )

    result = await session.execute(_user_q().where(User.id == user.id))
    return result.scalars().first()


@router.get("/me", response_model=UserOut, summary="Get the authenticated user")
async def get_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(_user_q().where(User.id == current_user.id))
    return result.scalars().first()


@router.put("/me", response_model=UserOut, summary="Update the authenticated user")
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if body.username and body.username != current_user.username:
        clash = await session.execute(
            select(User).where(User.username == body.username)
        )
        if clash.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
            )

    if body.mail and str(body.mail) != current_user.mail:
        clash = await session.execute(select(User).where(User.mail == str(body.mail)))
        if clash.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already taken"
            )

    for field, value in body.model_dump(exclude_none=True).items():
        if field == "password":
            setattr(current_user, "password", hash_password(value))
        elif field == "mail":
            setattr(current_user, "mail", str(value))
        else:
            setattr(current_user, field, value)

    await session.commit()
    result = await session.execute(_user_q().where(User.id == current_user.id))
    return result.scalars().first()


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete the authenticated user",
)
async def delete_me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    await session.delete(current_user)
    await session.commit()


@router.get("/", response_model=list[UserOut], summary="List all users")
async def get_all_users(
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(_user_q())
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserOut, summary="Get a user by ID")
async def get_user(
    user_id: int,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(_user_q().where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user by ID"
)
async def delete_user(
    user_id: int,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    await session.delete(user)
    await session.commit()


# ---------------------------------------------------------------------------
# Notifications  (scoped to the authenticated user)
# ---------------------------------------------------------------------------


@router.get(
    "/notification/",
    response_model=list[NotificationOut],
    summary="Get all notifications",
)
async def get_notifications(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Notification).where(Notification.user_id == current_user.id)
    )
    return result.scalars().all()


@router.put(
    "/notification/read/{notification_id}",
    response_model=NotificationOut,
    summary="Mark a notification as read",
)
async def read_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    notif.read = True
    await session.commit()
    await session.refresh(notif)
    return notif


@router.put(
    "/notification/unread/{notification_id}",
    response_model=NotificationOut,
    summary="Mark a notification as unread",
)
async def unread_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    notif.read = False
    await session.commit()
    await session.refresh(notif)
    return notif


@router.get(
    "/notification/{notification_id}",
    response_model=NotificationOut,
    summary="Get a specific notification",
)
async def get_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    return notif


@router.delete(
    "/notification/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a notification",
)
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    await session.delete(notif)
    await session.commit()


# ---------------------------------------------------------------------------
# Reminders  (scoped to the authenticated user)
# ---------------------------------------------------------------------------


@router.post(
    "/reminder/",
    response_model=ReminderOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reminder",
)
async def create_reminder(
    body: ReminderCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    reminder = Reminder(
        user_id=current_user.id,
        date=body.date,
        title=body.title,
        description=body.description,
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return reminder


@router.get("/reminder/", response_model=list[ReminderOut], summary="Get all reminders")
async def get_reminders(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Reminder).where(Reminder.user_id == current_user.id)
    )
    return result.scalars().all()


@router.delete(
    "/reminder/", status_code=status.HTTP_204_NO_CONTENT, summary="Delete all reminders"
)
async def delete_all_reminders(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Reminder).where(Reminder.user_id == current_user.id)
    )
    for reminder in result.scalars().all():
        await session.delete(reminder)
    await session.commit()


@router.get(
    "/reminder/{reminder_id}",
    response_model=ReminderOut,
    summary="Get a specific reminder",
)
async def get_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )
    return reminder


@router.delete(
    "/reminder/{reminder_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a specific reminder",
)
async def delete_reminder(
    reminder_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found"
        )
    await session.delete(reminder)
    await session.commit()
