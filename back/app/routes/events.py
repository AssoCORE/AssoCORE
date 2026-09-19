from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, require_admin, require_roles
from app.core.notifications import notify, notify_many
from app.core.pagination import limit_param, offset_param, paginate
from app.db.database import get_session
from app.db.models import Event, User
from app.schemas.classes import EventCreate, EventOut, EventUpdate, Page

router = APIRouter(prefix="/event", tags=["event"])


def _event_q():
    return select(Event).options(
        selectinload(Event.registered_users),
        selectinload(Event.staff),
        selectinload(Event.attendees),
    )


def _to_schema(event: Event) -> EventOut:
    registered_count = len(event.registered_users)
    spots_left = max(0, event.registrations_limits - registered_count)
    return EventOut(
        id=event.id,
        title=event.title,
        description=event.description,
        start_date=event.start_date,
        end_date=event.end_date,
        registrations_limits=event.registrations_limits,
        creator_id=event.creator_id,
        registered_count=registered_count,
        spots_left=spots_left,
        is_full=spots_left == 0,
        registered_user_ids=[u.id for u in event.registered_users],
        staff_ids=[u.id for u in event.staff],
        attendee_ids=[u.id for u in event.attendees],
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_model=Page[EventOut], summary="List events")
async def list_events(
    upcoming: bool = Query(default=False, description="Only future events"),
    past: bool = Query(default=False, description="Only past events"),
    my_events: bool = Query(
        default=False, description="Only events I am registered for"
    ),
    q: str | None = Query(
        default=None, description="Case-insensitive search in title and description"
    ),
    limit: int = limit_param(),
    offset: int = offset_param(),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    stmt = _event_q()
    now = datetime.now(timezone.utc)
    if upcoming:
        stmt = stmt.where(Event.start_date > now)
    elif past:
        stmt = stmt.where(Event.end_date < now)
    if q:
        term = f"%{q}%"
        stmt = stmt.where(or_(Event.title.ilike(term), Event.description.ilike(term)))
    if my_events:
        # Filter in SQL rather than loading every event and checking in Python —
        # otherwise limit/offset would page over the wrong set.
        stmt = stmt.where(Event.registered_users.any(User.id == current_user.id))
    return await paginate(
        session, stmt.order_by(Event.start_date), limit, offset, transform=_to_schema
    )


@router.get("/{event_id}", response_model=EventOut, summary="Get a specific event")
async def get_event(
    event_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(_event_q().where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    return _to_schema(event)


@router.post(
    "/",
    response_model=EventOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event (admin/staff)",
)
async def create_event(
    body: EventCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    event = Event(
        creator_id=current_user.id,
        title=body.title,
        description=body.description,
        start_date=body.start_date,
        end_date=body.end_date,
        registrations_limits=body.registrations_limits,
    )
    session.add(event)
    await session.commit()
    result = await session.execute(_event_q().where(Event.id == event.id))
    return _to_schema(result.scalar_one())


@router.put(
    "/{event_id}",
    response_model=EventOut,
    summary="Update an event (admin/staff or creator)",
)
async def update_event(
    event_id: int,
    body: EventUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(_event_q().where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    is_privileged = any(r.name in ("admin", "staff") for r in current_user.roles)
    if not is_privileged and event.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(event, field, value)

    if event.end_date <= event.start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be after start_date",
        )

    await session.commit()
    result = await session.execute(_event_q().where(Event.id == event.id))
    updated = result.scalar_one()

    await notify_many(
        session,
        [u.id for u in updated.registered_users],
        f'The event "{updated.title}" has been updated',
        from_id=current_user.id,
    )
    return _to_schema(updated)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event (admin only)",
)
async def delete_event(
    event_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_admin),
):
    # Eager-loaded so the registrants can be read here — after the delete they
    # are gone, and on an async session a lazy load would raise MissingGreenlet.
    result = await session.execute(_event_q().where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    registered_ids = [u.id for u in event.registered_users]
    title = event.title

    await session.delete(event)
    await session.commit()

    await notify_many(
        session,
        registered_ids,
        f'The event "{title}" has been cancelled',
        from_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# Self-registration
# ---------------------------------------------------------------------------


@router.post(
    "/{event_id}/register",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Register current user for an event",
)
async def register_for_event(
    event_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(_event_q().where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    if any(u.id == current_user.id for u in event.registered_users):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already registered"
        )

    if len(event.registered_users) >= event.registrations_limits:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Event is full"
        )

    event.registered_users.append(current_user)
    await session.commit()

    await notify(
        session,
        current_user.id,
        f'You are registered for "{event.title}"',
    )


@router.delete(
    "/{event_id}/register",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister current user from an event",
)
async def unregister_from_event(
    event_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    result = await session.execute(_event_q().where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    registered = next(
        (u for u in event.registered_users if u.id == current_user.id), None
    )
    if registered is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not registered for this event",
        )

    event.registered_users.remove(registered)
    await session.commit()


# ---------------------------------------------------------------------------
# Check-in / attendance (F4)
# ---------------------------------------------------------------------------


@router.post(
    "/{event_id}/checkin/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Check in a user (admin/staff)",
)
async def checkin_user(
    event_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    result = await session.execute(_event_q().where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if any(u.id == user_id for u in event.attendees):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already checked in"
        )

    event.attendees.append(target)
    await session.commit()


@router.delete(
    "/{event_id}/checkin/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Undo a check-in (admin/staff)",
)
async def undo_checkin(
    event_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_roles("admin", "staff")),
):
    result = await session.execute(_event_q().where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )

    target = next((u for u in event.attendees if u.id == user_id), None)
    if target is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not checked in"
        )

    event.attendees.remove(target)
    await session.commit()
