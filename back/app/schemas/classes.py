import re
from datetime import datetime
from typing import Annotated, Optional, Dict, Any, List
from pydantic import (
    BaseModel,
    ConfigDict,
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
        max_length=255,
    ),
]


# Base schema for all models
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Role schemas
class RoleBase(BaseSchema):
    """Base schema for Role"""

    type: str = Field(..., max_length=255, description="Role type")


class RoleCreate(RoleBase):
    """Schema for creating a Role"""

    pass


class RoleResponse(RoleBase):
    """Schema for Role response"""

    id: int


# User schemas
class UserBase(BaseSchema):
    """Base schema for User"""

    user_id: int = Field(..., description="Link to Nextcloud user ID")
    name: str = Field(..., max_length=255, description="User's first name")
    last_name: str = Field(..., max_length=255, description="User's last name")
    additional_info: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional user information as JSON"
    )


class UserCreate(UserBase):
    """Schema for creating a User"""

    password: PasswordStr
    role_ids: List[int] = Field(default_factory=list, description="List of role IDs")


class UserUpdate(BaseSchema):
    """Schema for updating a User"""

    name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    password: Optional[PasswordStr] = None
    additional_info: Optional[Dict[str, Any]] = None
    role_ids: Optional[List[int]] = None


class UserResponse(UserBase):
    """Schema for User response"""

    id: int
    created_at: datetime
    roles: List[RoleResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Notification schemas
class NotificationBase(BaseSchema):
    """Base schema for Notification"""

    message: str
    from_id: Optional[int] = None


class NotificationCreate(NotificationBase):
    """Schema for creating a Notification"""

    pass


class NotificationResponse(NotificationBase):
    """Schema for Notification response"""

    id: int
    user_id: int
    date: datetime
    read: bool


# Reminder schemas
class ReminderBase(BaseSchema):
    """Base schema for Reminder"""

    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    date: datetime


class ReminderCreate(ReminderBase):
    """Schema for creating a Reminder"""

    pass


class ReminderUpdate(BaseSchema):
    """Schema for updating a Reminder"""

    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    date: Optional[datetime] = None


class ReminderResponse(ReminderBase):
    """Schema for Reminder response"""

    id: int
    user_id: int


# Event schemas
class EventBase(BaseSchema):
    """Base schema for Event"""

    title: str = Field(..., max_length=255, description="Event title")
    extended_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Extended event data as JSON"
    )
    start: datetime = Field(..., description="Event start date and time")
    end: datetime = Field(..., description="Event end date and time")

    @field_validator("end")
    @classmethod
    def validate_event_dates(cls, v: datetime, info) -> datetime:
        start = info.data.get("start")
        if start and v <= start:
            raise ValueError("end must be after start")
        return v


class EventCreate(EventBase):
    """Schema for creating an Event"""

    staff_ids: List[int] = Field(
        default_factory=list, description="List of staff user IDs"
    )
    user_ids: List[int] = Field(
        default_factory=list, description="List of registered user IDs"
    )


class EventUpdate(BaseSchema):
    """Schema for updating an Event"""

    title: Optional[str] = Field(None, max_length=255)
    extended_data: Optional[Dict[str, Any]] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    staff_ids: Optional[List[int]] = None
    user_ids: Optional[List[int]] = None

    @field_validator("end")
    @classmethod
    def validate_event_dates(cls, v: Optional[datetime], info) -> Optional[datetime]:
        if v is not None:
            start = info.data.get("start")
            if start and v <= start:
                raise ValueError("end must be after start")
        return v


class EventResponse(EventBase):
    """Schema for Event response"""

    id: int
    created_at: datetime
    creator_id: Optional[int] = None


# Extended response schemas with nested relationships (optional, for detailed views)
class UserDetailedResponse(UserResponse):
    """Detailed User response with relationships"""

    notifications: List[NotificationResponse] = Field(default_factory=list)
    reminders: List[ReminderResponse] = Field(default_factory=list)


class EventDetailedResponse(EventResponse):
    """Detailed Event response with relationships"""

    creator: Optional[UserResponse] = None
    staff: List[UserResponse] = Field(default_factory=list)
    users: List[UserResponse] = Field(default_factory=list)
