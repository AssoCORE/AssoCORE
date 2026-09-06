from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.dependencies import get_current_user, require_admin, require_roles
from app.db.database import get_session
from app.db.models import Event, User
from app.schemas.classes import EventCreate, EventOut, EventUpdate

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


@router.get("/", response_model=list[EventOut], summary="List events")
async def list_events(
    upcoming: bool = Query(default=False, description="Only future events"),
    past: bool = Query(default=False, description="Only past events"),
    my_events: bool = Query(
        default=False, description="Only events I am registered for"
    ),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from datetime import datetime, timezone

    q = _event_q()
    now = datetime.now(timezone.utc)
    if upcoming:
        q = q.where(Event.start_date > now)
    elif past:
        q = q.where(Event.end_date < now)
    result = await session.execute(q.order_by(Event.start_date))
    events = result.scalars().all()
    if my_events:
        events = [
            e
            for e in events
            if any(u.id == current_user.id for u in e.registered_users)
        ]
    return [_to_schema(e) for e in events]


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
    return _to_schema(result.scalar_one())


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
    result = await session.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        )
    await session.delete(event)
    await session.commit()


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
