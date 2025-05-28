from __future__ import annotations

import os
import shutil
import sys
import tkinter as tk

from loguru import logger

from business import appsupportdir, get_con, initialize_user
from constants import DB_ENVIRONMENT


def get_db_paths() -> tuple[os.PathLike]:
    """
    Function to get paths to db and temporary database backup.

    Returns tuple[os.PathLike]: A 2 tuple containing the path to the database
    and the path to the database backup.
    """
    # Check that DB_ENVIRONMENT is valid.
    if DB_ENVIRONMENT not in ["production", "test"]:
        logger.warning("Invalid DB_ENVIRONMENT, exiting.")
        sys.exit()
    # Get the database path depending on the database environment.
    if DB_ENVIRONMENT != "production":
        try:
            db_path = os.path.join(os.path.dirname(__file__), "test.db")
        except FileNotFoundError as e:
            logger.error(f"Test database not found: {e}, exiting.")
            sys.exit()
    else:
        try:
            dir_path = os.path.join(appsupportdir(), "Home Reminders")
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            db_path = os.path.join(dir_path, "home_reminders.db")
        except FileNotFoundError as e:
            logger.error(f"Production database not found: {e}, exiting.")
            sys.exit()
    # Create a path to temporarily backup the database.
    db_bak_path = os.path.join(os.path.dirname(__file__), "db_backup.tmp")
    return (db_path, db_bak_path)


def test_initialize_user():
    """
    Test the initialize_user function.
    """
    db_path = get_db_paths()[0]
    db_bak_path = get_db_paths()[1]
    logger.info(f"db_bak_path: {db_bak_path}")
    # Create a temporary database backup.
    shutil.copy2(db_path, db_bak_path)

    # Mock the app.
    app = tk.Tk()

    try:
        with get_con() as con:
            cur = con.cursor()
            # Temporarily empty the user table.
            cur.execute("DELETE FROM user")
            con.commit()
            # Run the function.
            initialize_user(app)
            # Check that user table now has the initialized values.
            user = cur.execute("SELECT * FROM user").fetchone()
            logger.info(f"initialized user: {user}")
            assert user
            assert user[0] == ""
            assert user[1] == 0
            assert user[2] == 0
            assert user[3] == 0
            assert user[4] == "1970-01-01"
            # Check that initialize_user function does nothing if the user
            # table is not empty. Start by emptying user table and inserting
            # a new set of user values.
            cur.execute("DELETE FROM user")
            values = ("1234567890", 1, 1, 1, "2025-05-28")
            cur.execute(
                """
                    INSERT INTO user (
                        phone_number,
                        week_before,
                        day_before,
                        day_of,
                        last_notification_date)
                        VALUES (?, ?, ?, ?, ?)""",
                values,
            )
            con.commit()
            user = cur.execute("SELECT * FROM user").fetchone()
            logger.info(f"inserted user: {user}")
            # Run the function and confirm that the new values are unchanged.
            initialize_user(app)
            assert user
            assert user[0] == "1234567890"
            assert user[1] == 1
            assert user[2] == 1
            assert user[3] == 1
            assert user[4] == "2025-05-28"
    except Exception as e:
        logger.error(
            f"Error occurred while testing the initialize_user function: {e}."
        )
        sys.exit()
    finally:
        # Restore the database to it's original state.
        shutil.copy2(db_bak_path, db_path)
        # Delete the temporary database backup.
        os.remove(db_bak_path)
        app.destroy()
