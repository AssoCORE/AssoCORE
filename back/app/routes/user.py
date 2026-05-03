import os
import jwt
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from nc_py_api import Nextcloud

from app.db.database import get_session
from app.db.models import User, Notification, Reminder
from app.schemas.classes import (
    UserCreate,
    UserUpdate,
    UserOut,
    NotificationOut,
    ReminderCreate,
    ReminderOut,
)

router = APIRouter(prefix="/user", tags=["user"])


def _user_q():
    """select(User) with all relationships eagerly loaded."""
    return select(User).options(
        selectinload(User.roles),
        selectinload(User.notifications),
        selectinload(User.reminders),
    )


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-secure-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/login")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    result = await session.execute(_user_q().where(User.username == username))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------


@router.post("/login", description="Login via Nextcloud credentials")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
):
    try:
        nc_url = os.getenv("NEXTCLOUD_URL", "http://nextcloud")
        nc = Nextcloud(
            nextcloud_url=nc_url,
            nc_auth_user=form_data.username,
            nc_auth_pass=form_data.password,
        )
        import nc_py_api

        try:
            nc.users.get_user()
        except nc_py_api.NextcloudException:
            raise ValueError("Invalid Nextcloud credentials")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await session.execute(_user_q().where(User.username == form_data.username))
    local_user = result.scalars().first()
    if not local_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User authenticated in Nextcloud but has no local AssoCORE profile.",
        )
    if not verify_password(form_data.password, local_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# USER CRUD
# ---------------------------------------------------------------------------


@router.post("/create", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    existing = await session.execute(
        _user_q().where((User.username == body.username) | (User.mail == body.mail))
    )
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Username or email already taken.")

    user = User(
        name=body.name,
        firstname=body.firstname,
        username=body.username,
        password=hash_password(body.password),
        mail=body.mail,
        phone=body.phone,
        age=body.age,
    )
    session.add(user)
    await session.commit()
    result = await session.execute(_user_q().where(User.id == user.id))
    return result.scalars().first()


@router.get("/", response_model=list[UserOut])
async def get_all_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    result = await session.execute(_user_q())
    return result.scalars().all()


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    result = await session.execute(_user_q().where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.put("/update", response_model=UserOut)
async def update_user(
    body: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    await session.commit()
    result = await session.execute(_user_q().where(User.id == current_user.id))
    return result.scalars().first()


@router.delete("/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
):
    result = await session.execute(_user_q().where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await session.delete(user)
    await session.commit()


# ---------------------------------------------------------------------------
# NOTIFICATIONS  (must be declared before /{user_id} to avoid route conflict)
# ---------------------------------------------------------------------------


@router.get("/notification/", response_model=list[NotificationOut])
async def get_notifications(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Notification).where(Notification.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/notification/{notification_id}", response_model=NotificationOut)
async def get_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    return notif


@router.put("/notification/read/{notification_id}", response_model=NotificationOut)
async def read_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.read = True
    await session.commit()
    await session.refresh(notif)
    return notif


@router.put("/notification/unread/{notification_id}", response_model=NotificationOut)
async def unread_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.read = False
    await session.commit()
    await session.refresh(notif)
    return notif


@router.delete(
    "/notification/{notification_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_notification(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    await session.delete(notif)
    await session.commit()


# ---------------------------------------------------------------------------
# REMINDERS
# ---------------------------------------------------------------------------


@router.post(
    "/reminder/", response_model=ReminderOut, status_code=status.HTTP_201_CREATED
)
async def create_reminder(
    body: ReminderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
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


@router.get("/reminder/", response_model=list[ReminderOut])
async def get_reminders(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Reminder).where(Reminder.user_id == current_user.id)
    )
    return result.scalars().all()


@router.get("/reminder/{reminder_id}", response_model=ReminderOut)
async def get_reminder(
    reminder_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    return reminder


@router.delete("/reminder/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_reminders(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Reminder).where(Reminder.user_id == current_user.id)
    )
    for reminder in result.scalars().all():
        await session.delete(reminder)
    await session.commit()


@router.delete("/reminder/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_reminder(
    reminder_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(
        select(Reminder).where(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
    )
    reminder = result.scalars().first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    await session.delete(reminder)
    await session.commit()
