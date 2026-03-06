from datetime import datetime
from typing import List

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    Table,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from .database import Base


# Association tables
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    ),
)

event_registrations = Table(
    "event_registrations",
    Base.metadata,
    Column(
        "event_id",
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
)

event_staff = Table(
    "event_staff",
    Base.metadata,
    Column(
        "event_id",
        Integer,
        ForeignKey("events.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Role id={self.id} name={self.name!r}>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    firstname = Column(String(128), nullable=False)
    username = Column(String(128), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    mail = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(16), nullable=True)
    age = Column(Integer, nullable=True)

    # relationships
    roles = relationship("Role", secondary=user_roles, backref="users")
    notifications = relationship(
        "Notification", back_populates="owner", cascade="all, delete-orphan"
    )
    reminders = relationship(
        "Reminder", back_populates="owner", cascade="all, delete-orphan"
    )

    created_events = relationship(
        "Event", back_populates="creator", cascade="all, delete-orphan"
    )
    registered_events = relationship(
        "Event", secondary=event_registrations, back_populates="registered_users"
    )
    staff_events = relationship("Event", secondary=event_staff, back_populates="staff")

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r}>"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date = Column(DateTime, default=datetime.now(datetime.timezone.utc), nullable=False)
    message = Column(Text, nullable=False)
    from_id = Column(Integer, nullable=True)
    read = Column(Boolean, default=False, nullable=False)

    owner = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id}>"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date = Column(DateTime, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    owner = relationship("User", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} user_id={self.user_id} title={self.title!r}>"


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    creator_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    registrations_limits = Column(Integer, nullable=False)

    creator = relationship("User", back_populates="created_events")
    registered_users = relationship(
        "User", secondary=event_registrations, back_populates="registered_events"
    )
    staff = relationship("User", secondary=event_staff, back_populates="staff_events")

    def __repr__(self) -> str:
        return f"<Event id={self.id} title={self.title!r}>"
