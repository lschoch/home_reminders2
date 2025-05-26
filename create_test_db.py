import sqlite3
import sys

from loguru import logger

values1 = (
    "test1",
    "1",
    "week",
    "2023-10-01",
    "2023-10-08",
    "note for test1",
)
values2 = (
    "test2",
    "1",
    "year",
    "2023-10-01",
    "2024-10-01",
    "note for test2",
)
try:
    with sqlite3.connect("./tests/test.db") as con:
        try:
            cur = con.cursor()
            # Drop the user and reminders tables if they exist so that new ones
            # can be created.
            cur.execute("DROP TABLE IF EXISTS user")
            cur.execute("DROP TABLE IF EXISTS reminders")
            # Create new user table to store user phone number and
            # notifications preferences, if it doesn't exist.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user(
                    phone_number TEXT,
                    week_before INT,
                    day_before INT,
                    day_of INT,
                    last_notification_date TEXT)
            """)
            # Create new reminders table to store reminders, if it doesn't
            # exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reminders(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    frequency TEXT,
                    period TEXT,
                    date_last TEXT,
                    date_next TEXT,
                    note TEXT)
            """)
            # Commit the changes
            con.commit()
        except sqlite3.Error as e:
            logger.error(f"Error creating test database tables: {e}, exiting.")
            sys.exit()
        try:
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
            con.commit()
            logger.info("Test database created successfully")
        except sqlite3.Error as e:
            logger.error(
                f"Error inserting data into test database: {e}, exiting."
            )
            sys.exit()
except sqlite3.Error as e:
    logger.error(f"Error connecting to test database: {e}, exiting.")
    sys.exit()
