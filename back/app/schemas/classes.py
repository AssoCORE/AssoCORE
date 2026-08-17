import re
from datetime import datetime
from typing import Annotated
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    StringConstraints,
    Field,
    field_validator,
)

PasswordStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=8,
        max_length=50,
        pattern=re.compile(
            r"^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
        ),
    ),
]


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --- Auth ---


class LoginRequest(BaseSchema):
    username: str
    password: str


class Token(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access_token expires


class RefreshRequest(BaseSchema):
    refresh_token: str


class LogoutRequest(BaseSchema):
    # Optional: without it only the current access token is revoked, and other devices in the
    # same session keep working until their refresh token expires.
    refresh_token: str | None = None


# --- Role ---


class RoleOut(BaseSchema):
    id: int
    name: str


# --- Notification ---


class NotificationOut(BaseSchema):
    id: int
    date: datetime
    message: str
    from_id: int | None
    read: bool


# --- Reminder ---


class ReminderCreate(BaseSchema):
    date: datetime
    title: str
    description: str | None = None


class ReminderOut(BaseSchema):
    id: int
    date: datetime
    title: str
    description: str | None


# --- User ---


class UserCreate(BaseSchema):
    name: str
    firstname: str
    username: str
    password: PasswordStr
    mail: EmailStr
    phone: str | None = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    birth_date: datetime | None = None


class UserUpdate(BaseSchema):
    name: str | None = None
    firstname: str | None = None
    username: str | None = None
    mail: EmailStr | None = None
    phone: str | None = Field(default=None, pattern=r"^\+?[1-9]\d{1,14}$")
    birth_date: datetime | None = None
    password: PasswordStr | None = None


class UserOut(BaseSchema):
    id: int
    name: str
    firstname: str
    username: str
    mail: str
    phone: str | None
    birth_date: datetime | None
    roles: list[RoleOut] = Field(default_factory=list)
    notifications: list[NotificationOut] = Field(default_factory=list)
    reminders: list[ReminderOut] = Field(default_factory=list)


# --- Nextcloud account linking ---


class NcLinkInit(BaseSchema):
    login_url: str  # open in a browser to approve
    handle: (
        str  # opaque server-side reference; the real poll token never leaves the API
    )
    expires_in: int


class NcLinkPoll(BaseSchema):
    status: str  # "pending" | "linked"
    nc_username: str | None = None


class NcLinkStatus(BaseSchema):
    linked: bool
    nc_username: str | None = None
    linked_at: datetime | None = None


# --- Storage ---


class FileNode(BaseSchema):
    name: str
    path: str
    is_dir: bool
    size: int
    mime_type: str
    last_modified: datetime
    etag: str
    file_id: str


class FolderCreate(BaseSchema):
    path: str


class MoveRequest(BaseSchema):
    src: str
    dst: str
    overwrite: bool = False


class CopyRequest(BaseSchema):
    src: str
    dst: str
    overwrite: bool = False


# --- Event ---


class EventCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime
    end_date: datetime
    registrations_limits: int = Field(..., gt=0)

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_date")
        if start and v <= start:
            raise ValueError("end_date must be after start_date")
        return v


class EventUpdate(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registrations_limits: int | None = Field(default=None, gt=0)


class EventOut(BaseSchema):
    id: int
    title: str
    description: str | None
    start_date: datetime
    end_date: datetime
    registrations_limits: int
    creator_id: int | None
    registered_count: int
    spots_left: int
    is_full: bool
    registered_user_ids: list[int]
    staff_ids: list[int]
    attendee_ids: list[int]
