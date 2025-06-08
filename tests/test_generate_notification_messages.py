import sqlite3
import tkinter as tk

import pytest
from loguru import logger  # noqa: F401

from business import (
    categorize_reminders,
    cleanup,
    copy_test_db,
    error_cleanup,
    generate_notification_messages,
    get_con,
    get_test_reminders,
)
from constants import DB_ENVIRONMENT


@pytest.mark.parametrize(
    "user_preferences, expected",
    [
        (("1234567890", 0, 0, 0, "1970-01-01"), ("\u2022 Past due: test1\n")),
        (
            ("1234567890", 0, 0, 1, "1970-01-01"),
            ("\u2022 Past due: test1\n\u2022 Due today: test2\n"),
        ),
        (
            ("1234567890", 0, 1, 0, "1970-01-01"),
            ("\u2022 Past due: test1\n\u2022 Due tomorrow: test3\n"),
        ),
        (
            ("1234567890", 1, 0, 0, "1970-01-01"),
            ("\u2022 Past due: test1\n\u2022 Due in 7 days: test4\n"),
        ),
        (
            ("1234567890", 1, 1, 0, "1970-01-01"),
            (
                "\u2022 Past due: test1\n\u2022 Due tomorrow: test3\n\u2022 "
                "Due in 7 days: test4\n"
            ),
        ),
        (
            ("1234567890", 1, 1, 1, "1970-01-01"),
            (
                "\u2022 Past due: test1\n\u2022 Due today: test2\n"
                "\u2022 Due tomorrow: test3\n\u2022 Due in 7 days: test4\n"
            ),
        ),
    ],
)
def test_generate_notification_messages(user_preferences, expected):
    # Skip this test if not in test environment.
    if DB_ENVIRONMENT != "test":
        pytest.skip("Skipping this test - not in test environment.")

    # Make a copy of the test database for restoration later.
    test_db_copy = copy_test_db()
    db_path = test_db_copy[0]
    db_bak_path = test_db_copy[1]

    app = tk.Tk()
    reminders = get_test_reminders()
    categorized_reminders = categorize_reminders(reminders)

    # Set user preferences - they  determine the reminders that get included in
    # the notification messages.
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("""DELETE FROM user""")
            con.commit()
            cur.execute(
                """
                    INSERT INTO user (
                        phone_number,
                        week_before,
                        day_before,
                        day_of,
                        last_notification_date)
                        VALUES (?, ?, ?, ?, ?)""",
                user_preferences,
            )
            con.commit()
    except sqlite3.Error as e:
        error_cleanup(
            app,
            db_path,
            db_bak_path,
            e,
            "Database error setting user preferences",
        )
    # Get message if there are no reminders.
    message_no_reminders = generate_notification_messages(app, None)
    # Get messages provided by get_reminders function.
    message = generate_notification_messages(app, categorized_reminders)

    # Restore test database now in case there is an assertion error.
    cleanup(app, db_path, db_bak_path)

    # Check the message if there are no categorized reminders.
    assert message_no_reminders == "No notifications.\n"
    # Check the message against expected for the given user preferences.
    assert message == expected
