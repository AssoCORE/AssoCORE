"""The background worker: the loop, the poller registry, and claimable rows."""

import asyncio
from contextlib import asynccontextmanager
from datetime import timedelta

import pytest
from sqlalchemy import Column, Integer, select

from app.core import worker as worker_mod
from app.core.worker import (
    DONE,
    FAILED,
    PENDING,
    PROCESSING,
    Poller,
    QueueRowMixin,
    Worker,
    claim,
    complete,
    fail,
    register_poller,
    utcnow,
)
from app.db.database import Base


class _Job(QueueRowMixin, Base):
    """Test-only claimable table (created with the rest by conftest)."""

    __tablename__ = "test_worker_jobs"
    id = Column(Integer, primary_key=True)


@pytest.fixture
def factory(db_session):
    """A session factory that hands every poller the test session."""

    @asynccontextmanager
    async def _session():
        yield db_session

    return _session


def _worker(factory, *pollers: Poller, interval: float = 0.05) -> Worker:
    return Worker(factory, interval=interval, pollers={p.name: p for p in pollers})


def _counting(name: str, results: list[int], every=None) -> tuple[Poller, list]:
    calls = []

    async def tick(session):
        calls.append(session)
        return results[min(len(calls), len(results)) - 1]

    return Poller(name, tick, every), calls


# --- registry ---


def test_register_refuses_duplicate_names(monkeypatch):
    monkeypatch.setattr(worker_mod, "_pollers", {})

    async def tick(session):
        return 0

    register_poller("dup", tick)
    with pytest.raises(ValueError):
        register_poller("dup", tick)


# --- one pass ---


async def test_run_once_calls_every_poller_and_sums_their_work(factory, db_session):
    a, a_calls = _counting("a", [2])
    b, b_calls = _counting("b", [3])
    w = _worker(factory, a, b)

    assert await w.run_once() == 5
    assert len(a_calls) == len(b_calls) == 1
    assert a_calls[0] is db_session  # each tick gets a session from the factory
    assert w.last_tick_at is not None


async def test_a_failing_poller_does_not_stop_the_others(factory, caplog):
    async def boom(session):
        raise RuntimeError("broken feature")

    ok, ok_calls = _counting("ok", [1])
    w = _worker(factory, Poller("boom", boom), ok)

    assert await w.run_once() == 1
    assert len(ok_calls) == 1
    assert "Poller boom failed" in caplog.text


async def test_periodic_poller_waits_its_period_once_idle(factory):
    daily, calls = _counting("daily", [0], every=timedelta(days=1))
    w = _worker(factory, daily)

    await w.run_once()
    await w.run_once()
    assert len(calls) == 1  # found nothing, so not due again for a day


async def test_periodic_poller_keeps_going_while_it_finds_work(factory):
    # A purge deleting in batches drains its backlog in one go.
    daily, calls = _counting("daily", [100, 100, 0], every=timedelta(days=1))
    w = _worker(factory, daily)

    for _ in range(5):
        await w.run_once()
    assert len(calls) == 3


# --- the loop ---


async def test_loop_sleeps_when_idle_and_stops_cleanly(factory):
    idle, calls = _counting("idle", [0])
    w = _worker(factory, idle, interval=0.05)

    w.start()
    await asyncio.sleep(0.18)
    await w.stop()

    # About one call per interval, not a busy loop.
    assert 2 <= len(calls) <= 6
    assert not w.heartbeat()["running"]


async def test_loop_runs_again_at_once_when_there_is_work(factory):
    busy, calls = _counting("busy", [1] * 30 + [0])
    w = _worker(factory, busy, interval=10)  # a sleep would take 10 s

    w.start()
    for _ in range(100):
        if len(calls) > 30:
            break
        await asyncio.sleep(0.01)
    await w.stop()
    assert len(calls) > 30


async def test_stop_interrupts_the_idle_sleep(factory):
    idle, _ = _counting("idle", [0])
    w = _worker(factory, idle, interval=60)
    w.start()
    await asyncio.sleep(0.02)

    await asyncio.wait_for(w.stop(), timeout=1)  # well under the 60 s interval


async def test_heartbeat(factory):
    w = _worker(factory, _counting("x", [0])[0])
    assert w.heartbeat() == {
        "running": False,
        "last_tick_at": None,
        "seconds_since_tick": None,
    }
    await w.run_once()
    beat = w.heartbeat()
    assert beat["last_tick_at"].endswith("Z")
    assert beat["seconds_since_tick"] < 5


async def test_health_reports_the_worker(client):
    body = (await client.get("/health")).json()
    assert body["status"] == "ok"
    assert set(body["worker"]) == {"running", "last_tick_at", "seconds_since_tick"}


# --- claimable rows ---


@pytest.fixture
async def jobs(db_session):
    """Start every claim test from an empty table."""
    for row in (await db_session.execute(select(_Job))).scalars():
        await db_session.delete(row)
    await db_session.commit()
    yield


async def _add(db_session, **values) -> _Job:
    row = _Job(**values)
    db_session.add(row)
    await db_session.commit()
    return row


async def test_claim_takes_due_rows_and_leases_them(db_session, jobs):
    due = await _add(db_session)
    later = await _add(db_session, run_at=utcnow() + timedelta(hours=1))

    claimed = await claim(db_session, _Job, lease=timedelta(minutes=5))

    assert [r.id for r in claimed] == [due.id]
    assert due.status == PROCESSING
    assert due.attempts == 1
    assert due.locked_until > utcnow() + timedelta(minutes=4)
    assert later.status == PENDING
    # A leased row isn't handed out twice.
    assert await claim(db_session, _Job) == []


async def test_claim_respects_the_batch_size_and_order(db_session, jobs):
    rows = [await _add(db_session) for _ in range(5)]
    claimed = await claim(db_session, _Job, batch=2)
    assert [r.id for r in claimed] == [rows[0].id, rows[1].id]


async def test_an_expired_lease_is_claimed_again(db_session, jobs):
    # Its worker died mid-job: the row comes back once the lease runs out.
    stuck = await _add(
        db_session,
        status=PROCESSING,
        attempts=1,
        locked_until=utcnow() - timedelta(seconds=1),
    )
    claimed = await claim(db_session, _Job)
    assert [r.id for r in claimed] == [stuck.id]
    assert stuck.attempts == 2


async def test_complete_marks_the_row_done(db_session, jobs):
    row = await _add(db_session)
    (claimed,) = await claim(db_session, _Job)
    await complete(db_session, claimed)
    assert (row.status, row.locked_until) == (DONE, None)
    assert await claim(db_session, _Job) == []


async def test_fail_retries_with_backoff_then_gives_up(db_session, jobs):
    row = await _add(db_session)

    (claimed,) = await claim(db_session, _Job)
    await fail(
        db_session, claimed, ValueError("smtp down"), max_attempts=2,
        base_delay=timedelta(seconds=30),
    )
    assert row.status == PENDING
    assert row.last_error == "ValueError: smtp down"
    assert utcnow() + timedelta(seconds=20) < row.run_at
    assert await claim(db_session, _Job) == []  # not due until the backoff ends

    row.run_at = utcnow()  # fast-forward
    await db_session.commit()
    (claimed,) = await claim(db_session, _Job)
    await fail(db_session, claimed, ValueError("still down"), max_attempts=2)
    assert row.status == FAILED
    assert row.attempts == 2
    assert await claim(db_session, _Job) == []


async def test_backoff_doubles_each_attempt(db_session, jobs):
    row = await _add(db_session, attempts=2)  # this claim is attempt 3
    (claimed,) = await claim(db_session, _Job)
    before = utcnow()
    await fail(db_session, claimed, OSError("x"), base_delay=timedelta(seconds=10))
    delay = (row.run_at - before).total_seconds()
    assert 39 <= delay <= 41  # 10 s * 2 ** (3 - 1)
