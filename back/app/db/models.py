from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    Table,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from .database import Base


# Association tables for many-to-many relationships
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

event_users = Table(
    "event_users",
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
    """Role model for user permissions"""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(255), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Role id={self.id} type={self.type!r}>"


class User(Base):
    """User model linked to Nextcloud users"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, nullable=False, index=True, comment="Link to Nextcloud user ID"
    )
    name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    additional_info = Column(
        JSON, nullable=True, comment="Additional user data as JSON"
    )

    # Relationships
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
        "Event", secondary=event_users, back_populates="users"
    )
    staff_events = relationship("Event", secondary=event_staff, back_populates="staff")

    def __repr__(self) -> str:
        return f"<User id={self.id} user_id={self.user_id} name={self.name!r} {self.last_name!r}>"


class Notification(Base):
    """Notification model for user notifications"""

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    message = Column(Text, nullable=False)
    from_id = Column(Integer, nullable=True)
    read = Column(Boolean, default=False, nullable=False)

    owner = relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification id={self.id} user_id={self.user_id}>"


class Reminder(Base):
    """Reminder model for user reminders"""

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date = Column(DateTime(timezone=True), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    owner = relationship("User", back_populates="reminders")

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} user_id={self.user_id} title={self.title!r}>"


class Event(Base):
    """Event model for managing events"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    extended_data = Column(JSON, nullable=True, comment="Extended event data as JSON")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    start = Column(DateTime(timezone=True), nullable=False)
    end = Column(DateTime(timezone=True), nullable=False)
    creator_id = Column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    creator = relationship("User", back_populates="created_events")
    users = relationship(
        "User", secondary=event_users, back_populates="registered_events"
    )
    staff = relationship("User", secondary=event_staff, back_populates="staff_events")

    def __repr__(self) -> str:
        return f"<Event id={self.id} title={self.title!r}>"
