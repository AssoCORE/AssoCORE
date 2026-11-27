"""The background worker: one in-process loop that drives every poller.

There is no broker. Domain rows are the queue (a newsletter's delivery rows, a
document waiting to be rendered, ...), and features register **pollers** that
process a few of them per call. Redis doesn't persist in our deployments, so a
redis queue would silently drop work on restart; the database doesn't.

Registering a poller, at import time of a module the app loads at startup::

    @poller("purge_role_history", every=timedelta(days=1))
    async def purge(session: AsyncSession) -> int:
        return await purge_role_history(session)

`tick(session)` returns how many rows it processed. The loop calls every due
poller in turn, loops again straight away when any of them found work, and
otherwise sleeps `WORKER_INTERVAL_SECONDS`. A poller with `every` runs at most
once per period, but keeps running while it still finds work, so a batched
purge drains its backlog instead of doing one batch a day.

Rows that need claiming across the backend replicas use `QueueRowMixin` with
`claim()`, `complete()` and `fail()`: `SELECT ... FOR UPDATE SKIP LOCKED` plus a
lease, so a row whose worker died is picked up again once the lease expires.
Delivery is therefore at-least-once: a poller's work must be safe to repeat for
the row that was in flight during a crash.

Logs carry poller names and row IDs only, never row contents.
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Iterable

from sqlalchemy import Column, DateTime, Integer, String, and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

WORKER_INTERVAL_SECONDS = float(os.getenv("WORKER_INTERVAL_SECONDS", "5"))

log = logging.getLogger(__name__)

Tick = Callable[[AsyncSession], Awaitable[int]]


def utcnow() -> datetime:
    """Naive UTC, which is what the DateTime columns store and read back."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


@dataclass
class Poller:
    name: str
    tick: Tick
    every: timedelta | None = None
    # time.monotonic() of the last run that found nothing to do (see `due`).
    idle_since: float | None = None

    def due(self, now: float) -> bool:
        if self.every is None or self.idle_since is None:
            return True
        return now - self.idle_since >= self.every.total_seconds()


_pollers: dict[str, Poller] = {}


def register_poller(name: str, tick: Tick, every: timedelta | None = None) -> Tick:
    if name in _pollers:
        raise ValueError(f"Poller {name!r} is already registered")
    _pollers[name] = Poller(name, tick, every)
    return tick


def poller(name: str, *, every: timedelta | None = None):
    """Decorator form of `register_poller`."""

    def decorate(tick: Tick) -> Tick:
        return register_poller(name, tick, every)

    return decorate


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------


class Worker:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | Callable[[], Any],
        interval: float = WORKER_INTERVAL_SECONDS,
        pollers: dict[str, Poller] | None = None,
    ):
        self._session_factory = session_factory
        self._interval = interval
        self._pollers = _pollers if pollers is None else pollers
        self._stopping = asyncio.Event()
        self._task: asyncio.Task | None = None
        self.last_tick_at: datetime | None = None

    async def run_once(self) -> int:
        """Call every due poller once. Returns the rows processed in total."""
        total = 0
        for p in list(self._pollers.values()):
            now = time.monotonic()
            if not p.due(now):
                continue
            try:
                async with self._session_factory() as session:
                    done = await p.tick(session)
            except Exception:
                # One broken poller must not stop the others, nor the loop.
                log.warning("Poller %s failed", p.name, exc_info=True)
                done = 0
            # Stay due while there is work left; start the `every` period
            # only once a run finds nothing.
            p.idle_since = None if done else now
            total += done
        self.last_tick_at = utcnow()
        return total

    async def run(self) -> None:
        log.info("Worker started with %d poller(s)", len(self._pollers))
        while not self._stopping.is_set():
            try:
                busy = await self.run_once() > 0
            except Exception:
                log.warning("Worker tick failed", exc_info=True)
                busy = False
            if busy:
                await asyncio.sleep(0)  # let requests in between batches
                continue
            try:
                await asyncio.wait_for(self._stopping.wait(), self._interval)
            except asyncio.TimeoutError:
                pass
        log.info("Worker stopped")

    def start(self) -> asyncio.Task:
        self._stopping.clear()
        self._task = asyncio.create_task(self.run(), name="assocore-worker")
        return self._task

    async def stop(self, timeout: float = 10) -> None:
        """Ask the loop to stop after the current poller, then wait for it."""
        if self._task is None:
            return
        self._stopping.set()
        try:
            await asyncio.wait_for(self._task, timeout)
        except asyncio.TimeoutError:
            log.warning("Worker did not stop within %ss, cancelling it", timeout)
            self._task.cancel()
        self._task = None

    def heartbeat(self) -> dict:
        """For GET /health: shows a stalled loop without failing the probe."""
        age = (
            round((utcnow() - self.last_tick_at).total_seconds(), 1)
            if self.last_tick_at
            else None
        )
        return {
            "running": self._task is not None and not self._task.done(),
            "last_tick_at": self.last_tick_at.isoformat() + "Z"
            if self.last_tick_at
            else None,
            "seconds_since_tick": age,
        }


def _default_session_factory():
    # Imported lazily so importing this module (to register a poller) doesn't
    # build the MariaDB engine.
    from app.db.database import async_session

    return async_session()


worker = Worker(_default_session_factory)


# ---------------------------------------------------------------------------
# Claimable rows
# ---------------------------------------------------------------------------

PENDING, PROCESSING, DONE, FAILED = "pending", "processing", "done", "failed"


class QueueRowMixin:
    """Columns for a table whose rows the worker claims, retries and completes."""

    status = Column(String(16), default=PENDING, nullable=False, index=True)
    attempts = Column(Integer, default=0, nullable=False)
    run_at = Column(DateTime, default=utcnow, nullable=False, index=True)
    locked_until = Column(DateTime, nullable=True)
    # The exception's type and message: may hold what the row itself holds (an
    # address an SMTP server rejected, ...), so it lives and is purged with it.
    last_error = Column(String(500), nullable=True)


async def claim(
    session: AsyncSession,
    model: type,
    *,
    batch: int = 10,
    lease: timedelta = timedelta(minutes=5),
    where: Iterable = (),
) -> list:
    """Claim up to `batch` rows that are due, or whose lease has expired.

    Locks with SKIP LOCKED, so two replicas never claim the same row (MariaDB;
    SQLite ignores it, which is fine single-process). Commits the claim before
    returning: do the work outside this transaction, then `complete()` or
    `fail()` each row. Every claim counts as an attempt, so a row that keeps
    crashing its worker still ends up `failed`.
    """
    now = utcnow()
    stmt = (
        select(model)
        .where(
            or_(
                and_(model.status == PENDING, model.run_at <= now),
                and_(model.status == PROCESSING, model.locked_until < now),
            ),
            *where,
        )
        .order_by(model.run_at, model.id)
        .limit(batch)
        .with_for_update(skip_locked=True)
    )
    rows = list((await session.execute(stmt)).scalars().all())
    for row in rows:
        row.status = PROCESSING
        row.locked_until = now + lease
        row.attempts += 1
    await session.commit()
    return rows


async def complete(session: AsyncSession, row) -> None:
    row.status = DONE
    row.locked_until = None
    row.last_error = None
    await session.commit()


async def fail(
    session: AsyncSession,
    row,
    error: BaseException,
    *,
    max_attempts: int = 5,
    base_delay: timedelta = timedelta(seconds=30),
) -> None:
    """Record a failed attempt: retry with exponential backoff, or give up."""
    row.last_error = f"{type(error).__name__}: {error}"[:500]
    row.locked_until = None
    if row.attempts >= max_attempts:
        row.status = FAILED
    else:
        row.status = PENDING
        row.run_at = utcnow() + base_delay * 2 ** (row.attempts - 1)
    await session.commit()
    log.warning(
        "%s row %s failed (attempt %d/%d, %s): %s",
        type(row).__name__,
        row.id,
        row.attempts,
        max_attempts,
        row.status,
        type(error).__name__,
    )
