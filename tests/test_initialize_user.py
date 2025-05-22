import os
import shutil
import tkinter as tk

from business import appsupportdir, get_con, initialize_user


def test_initialize_user():
    """
    Test the initialize_user function.
    """
    # Create a temporary database backup.
    # Get the database path.
    db_base_path = os.path.join(appsupportdir(), "Home Reminders")
    db_path = os.path.join(db_base_path, "home_reminders.db")
    # Create a path to backup the database.
    db_bak_path = os.path.join(db_base_path, "home_reminders.tmp")
    shutil.copy2(db_path, db_bak_path)

    # Mock the app.
    app = tk.Tk()

    # Temporarily empty the user table and run tests.
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM user")
            cur.commit()
            initialize_user(app)
            cur.execute("SELECT * FROM user")
            user = cur.fetchone()
            assert user is not None
            assert user[0] == ""
            assert user[1] == 0
            assert user[2] == 0
            assert user[3] == 0
            assert user[4] is None
            # Check that initialize_user function does nothing if the user
            # table is not empty.
            cur.execute(
                """INSERT INTO user (phone_number) VALUES (?)""",
                ("1234567890",),
            )
            cur.commit()
            initialize_user(app)
            cur.execute("SELECT * FROM user")
            user = cur.fetchone()
            assert user is not None
            assert user[0] == "1234567890"
            assert user[1] == 0
            assert user[2] == 0
            assert user[3] == 0
            assert user[4] is None
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Restore the database and remove the temporary backup. This is
        # important to ensure that the test does not affect the actual database
        if os.path.exists(db_bak_path):
            os.remove(db_path)
            shutil.move(db_bak_path, db_path)
        app.destroy()
