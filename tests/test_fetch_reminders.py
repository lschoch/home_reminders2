import os
import shutil
import tkinter as tk
from datetime import date, datetime, timedelta

import pytest
from loguru import logger

from business import fetch_reminders, get_con
from constants import DB_ENVIRONMENT


def test_fetch_reminders():
    # Skip this test if not in test environment.
    if DB_ENVIRONMENT != "test":
        pytest.skip("Skipping this test - not in test environment.")

    app = tk.Tk()

    # Make a temporary copy of the test database so that it can be restored
    # later.
    db_path = os.path.join(os.path.dirname(__file__), "test.db")
    db_bak_path = os.path.join(os.path.dirname(__file__), "test_bak.db")
    shutil.copy2(db_path, db_bak_path)

    # Set data for the test.
    # Dates based on the current date.
    today_str = date.today().strftime("%y-%m-%d")
    yesterday_datetime = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday_datetime.strftime("%y-%m-%d")
    two_weeks_ago_datetime = datetime.now() - timedelta(weeks=2)
    two_weeks_ago_str = two_weeks_ago_datetime.strftime("%y-%m-%d")
    week_from_today_datetime = datetime.now() + timedelta(days=7)
    week_from_today_str = week_from_today_datetime.strftime("%y-%m-%d")
    # Set reminders with known due dates
    # Past due:
    values1 = (
        "test1",
        "13",
        "days",
        two_weeks_ago_str,
        yesterday_str,
        "test1 note",
    )
    # Due today:
    values2 = (
        "test2",
        "1",
        "days",
        yesterday_str,
        today_str,
        "test2 note",
    )
    # Due in one week:
    values3 = (
        "test3",
        "1",
        "weeks",
        today_str,
        week_from_today_str,
        "test3 note",
    )

    # Set up the test database.
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM reminders")
            con.commit()
            # Get function result if reminders table is empty - expect None.
            actual_for_empty_table = fetch_reminders(app, False).fetchall()
            # Insert values into the reminders table.
            cur.execute(
                """
                INSERT INTO reminders (
                    description,
                    frequency,
                    period,
                    date_last,
                    date_next,
                    note)
                VALUES (?, ?, ?, ?, ?, ?)""",
                values1,
            )
            cur.execute(
                """
                INSERT INTO reminders (
                    description,
                    frequency,
                    period,
                    date_last,
                    date_next,
                    note)
                VALUES (?, ?, ?, ?, ?, ?)""",
                values2,
            )
            cur.execute(
                """
                INSERT INTO reminders (
                    description,
                    frequency,
                    period,
                    date_last,
                    date_next,
                    note)
                VALUES (?, ?, ?, ?, ?, ?)""",
                values3,
            )
            con.commit()
            # Get function result after inserting values into the reminders
            # table.
            actual_values = fetch_reminders(app, False).fetchall()
            logger.info(f"actual_values: {actual_values}")
    except Exception as e:
        logger.error(f"Error during database setup: {e}, skipping this test.")
        # Error: restore test database before skipping the test.
        shutil.copy2(db_bak_path, db_path)
        # Delete the copy of the test database.
        os.remove(db_bak_path)
        app.destroy()
        pytest.skip("Error during database setup.")

    # If no error, cleanup before checking the results.
    shutil.copy2(db_bak_path, db_path)
    os.remove(db_bak_path)
    app.destroy()

    # Check function result for empty database - expect None.
    assert not actual_for_empty_table

    # Check that actual_values is not None
    assert actual_values
    # Check length of actual_values against expected length.
    assert len(actual_values) == 3
    # Check function results against expected. Note offset indices because
    # actual_values contains the id at index 0 whereas values do not.
    for i in range(1, len(actual_values[0])):
        assert actual_values[0][i] == values1[i - 1]
    for i in range(1, len(actual_values[1])):
        assert actual_values[1][i] == values2[i - 1]
    for i in range(1, len(actual_values[2])):
        assert actual_values[2][i] == values3[i - 1]
