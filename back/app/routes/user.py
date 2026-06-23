import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user
from app.core.nextcloud import provision_nc_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_session
from app.db.models import Notification, Reminder, User

log = logging.getLogger(__name__)
from app.schemas.classes import (
    LoginRequest,
    NotificationOut,
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


@router.post("/login", response_model=Token, summary="Authenticate and get a JWT")
async def login(body: LoginRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == body.username))
    user = result.scalars().first()
    if not user or not verify_password(body.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return Token(access_token=create_access_token(user.id))


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

    user = User(
        name=body.name,
        firstname=body.firstname,
        username=body.username,
        password=hash_password(body.password),
        mail=str(body.mail),
        phone=body.phone,
        birth_date=body.birth_date,
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
