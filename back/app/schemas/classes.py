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
    token_type: str = "bearer"


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


# --- Event ---


class Event(BaseSchema):
    registered_users: list[int] = Field(default_factory=list)
    staff: list[int] = Field(default_factory=list)
    creator_id: int | None
    start_date: datetime
    end_date: datetime
    title: str
    description: str | None
    registrations_limits: int = Field(..., gt=0)

    @field_validator("end_date")
    def validate_event_dates(cls, v, info):
        start_date = info.data.get("start_date")
        if start_date and v <= start_date:
            raise ValueError("end_date must be after start_date")
        return v
