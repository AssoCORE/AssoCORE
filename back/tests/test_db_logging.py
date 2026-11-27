"""SQL logging must never put personal data in the logs (#341)."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db import database


def test_sql_echo_is_off_by_default_and_parameters_are_hidden():
    assert database.SQL_ECHO is False  # SQL_ECHO is unset in the test environment
    assert database.engine.echo is False
    assert database.engine.sync_engine.hide_parameters is True


async def test_even_with_echo_on_bound_values_never_reach_the_log(caplog):
    # The same options the app engine uses, with echo forced on as SQL_ECHO=1 would.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=True, hide_parameters=True
    )
    caplog.set_level(logging.INFO, logger="sqlalchemy.engine")
    try:
        async with engine.connect() as conn:
            await conn.execute(
                text("SELECT :mail AS mail"), {"mail": "alice@example.com"}
            )
    finally:
        await engine.dispose()

    assert "SELECT" in caplog.text  # echo is on...
    assert "alice@example.com" not in caplog.text  # ...but the value is hidden
