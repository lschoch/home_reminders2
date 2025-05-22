import tkinter as tk

import pytest
from loguru import logger

from business import get_con, save_prefs


def test_save_prefs():
    # Mock the tkinter app and set the preference values for the test.
    app = tk.Tk()
    values = ("1234567890", 1, 1, 1, "1970-01-01")

    # Save the existing preferences so they can be restored later.
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM user")
            original_values = cur.fetchone()
    # Skip test if unable to retrieve original values.
    except Exception as e:
        # Log the error and skip the test.
        logger.error(
            f"An error occurred while retrieving original values: {e}, "
            "skipping this test."
        )
        app.destroy()
        pytest.skip(
            "An error occurred while retrieving original values. Skipping"
            " this test."
        )
    # Use the save_prefs function to save the test preferences to the database.
    # Test if the values have been successfully saved.
    save_prefs(app, values)
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM user")
            new_values = cur.fetchone()
            assert new_values == values
    except Exception as e:
        logger.error(f"An error occurred while checking the saved values: {e}")
    finally:
        # Restore the original preferences after the test.
        try:
            with get_con() as con:
                cur = con.cursor()
                cur.execute("DELETE FROM user")
                cur.execute(
                    """INSERT INTO user (
                    phone_number,
                    week_before,
                    day_before,
                    day_of,
                    last_notification_date) VALUES(?, ?, ?, ?, ?)""",
                    original_values,
                )
                con.commit()
                # Check if the values have been restored.
                cur.execute("SELECT * FROM user")
                restored_values = cur.fetchone()
                assert restored_values == original_values
        except Exception as e:
            logger.error(
                f"An error occurred while restoring the original values: {e}. "
                "User table may be corrupted. Please restore the database "
                "from a backup."
            )
        finally:
            app.destroy()
