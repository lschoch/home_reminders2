import sqlite3
import sys

import pytest


@pytest.fixture
def get_cursor():
    """values = (
        "test2",
        "1",
        "week",
        "2023-10-01",
        "2023-10-08",
        "test2 note",
    )"""
    try:
        with sqlite3.connect("./tests/test.db") as con:
            try:
                cur = con.cursor()
                # Create user table to store user phone number and
                # notifications preferences, if it doesn't exist.
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user(
                        phone_number TEXT,
                        week_before INT,
                        day_before INT,
                        day_of INT,
                        last_notification_date TEXT)
                """)
                # Create reminders table to store reminders, if it doesn't
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
            except sqlite3.Error as e:
                print(f"Error creating test database: {e}")
                sys.exit()
            '''
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
                    values,
                )
                con.commit()
            except sqlite3.Error as e:
                print(f"Error inserting data into test database: {e}")
                sys.exit()
            '''
            try:
                data = cur.execute("""SELECT * FROM reminders""")
                # Close the cursor and connection
                # Return the data
                return data
            except sqlite3.Error as e:
                print(f"Error retrieving data from test database: {e}")
                sys.exit()
    except sqlite3.Error as e:
        print(f"Error connecting to test database: {e}")
        sys.exit()
