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

# Define a custom type for password with specific constraints
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


# Base schema for all models
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Notification(BaseSchema):
    date: datetime
    message: str
    from_id: int
    read: bool


class Reminder(BaseSchema):
    date: datetime
    title: str
    description: str


class User(BaseSchema):
    notifications: list[Notification] = Field(
        default_factory=list, description="List of notifications"
    )
    reminders: list[Reminder] = Field(
        default_factory=list, description="List of reminders"
    )
    roles: list[int] = Field(default_factory=list, description="List of role IDs")
    name: str
    firstname: str
    username: str
    password: PasswordStr
    mail: EmailStr
    phone: str = Field(
        ..., regex=r"^\+?[1-9]\d{1,14}$", description="Phone number in E.164 format"
    )
    age: int = Field(..., ge=0, le=150, description="Age (0-150)")
    id: int = Field(..., gt=0, description="User ID (positive integer)")


class Event(BaseSchema):
    registered_users: list[int] = Field(
        default_factory=list, description="List of registered user IDs"
    )
    staff: list[int] = Field(default_factory=list, description="List of staff user IDs")
    creator: User
    start_date: datetime
    end_date: datetime
    title: str
    description: str
    registrations_limits: int = Field(
        ..., gt=0, description="Maximum number of registrations"
    )

    @field_validator("end_date")
    def validate_event_dates(cls, v, info):
        start_date = info.data.get("start_date")
        if start_date and v:
            if v <= start_date:
                raise ValueError("end_date must be after start_date")
        return v
