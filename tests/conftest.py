import sqlite3
import sys

import pytest
from _pytest.logging import LogCaptureFixture
from loguru import logger

from business import get_con


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,  # Set to 'True' if your test spawns child processes.
    )
    yield caplog
    logger.remove(handler_id)


@pytest.fixture
def reportlog(pytestconfig):
    logging_plugin = pytestconfig.pluginmanager.getplugin("logging-plugin")
    handler_id = logger.add(logging_plugin.report_handler, format="{message}")
    yield
    logger.remove(handler_id)


@pytest.fixture
def get_cursor():
    try:
        with get_con() as con:
            cur = con.cursor()
    except sqlite3.Error as e:
        logger.error(f"Error connecting to the test database: {e}, exiting.")
        sys.exit()
    try:
        return cur.execute("""SELECT * FROM reminders""")
    except sqlite3.Error as e:
        logger.error(
            f"Error retrieving data from test database: {e}, exiting."
        )
        sys.exit()
