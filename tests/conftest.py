import sqlite3
import sys

import pytest
from loguru import logger

from business import get_con


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
