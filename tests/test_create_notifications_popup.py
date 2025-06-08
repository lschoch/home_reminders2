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
from services2 import UIService


def test_create_notifications_popup():
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
    user_preferences = ("1234567890", 0, 0, 0, "1970-01-01")

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
    # Get the message if there are no reminders.
    message_no_reminders = generate_notification_messages(app, None)
    # Get messages provided by get_reminders function.
    message = generate_notification_messages(app, categorized_reminders)

    # Restore test database now in case there is an assertion error.
    cleanup(app, db_path, db_bak_path)

    # Create a notifications_popup window for no reminders.
    UIService.create_notifications_popup(app, message_no_reminders)

    def check_popup(msg):
        # Confirm that the popup window meets expected crteria.
        count = 0
        for popup in app.winfo_children():
            # Check the popup's class name.
            popup_type = type(popup)
            assert popup_type.__name__ == "NotificationsPopup"
            # Check content of the popup's text box.
            assert popup.txt.get("1.0", "end-1c") == msg
            if isinstance(popup, tk.Toplevel):
                count += 1
        # There should only be one Toplevel window open.
        assert count == 1

    check_popup("No notifications.\n")

    # Destroy current popup.
    for popup in app.winfo_children():
        popup.destroy()

    # Create a notifications_popup window for messages provided by
    # get_reminders function.
    UIService.create_notifications_popup(app, message)

    check_popup(message)
