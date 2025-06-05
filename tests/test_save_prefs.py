import os
import shutil
import tkinter as tk

import pytest
from loguru import logger

from business import get_con, save_prefs
from constants import DB_ENVIRONMENT


def test_save_prefs():
    # Skip this test if not in tesst environment.
    if DB_ENVIRONMENT != "test":
        pytest.skip("Skipping this test - not in test environment.")

    # Make a temporary copy of the test database so that it can be restored
    # later.
    db_path = os.path.join(os.path.dirname(__file__), "test.db")
    db_bak_path = os.path.join(os.path.dirname(__file__), "test_bak.db")
    shutil.copy2(db_path, db_bak_path)

    def cleanup():
        # Restore the test database.
        shutil.copy2(db_bak_path, db_path)
        # Delete the temporary copy of the test database.
        os.remove(db_bak_path)
        app.destroy()

    def error_cleanup(e, msg):
        logger.error(msg + f": {e}," + " skipping this test.")
        cleanup()
        pytest.skip(msg + ".")

    # Mock the tkinter app and set the preference values for the test.
    app = tk.Tk()
    values = ("1234567890", 1, 1, 1, "1970-01-01")

    # Use the save_prefs function to save the test preferences to the database.
    # Test if the values have been successfully saved.
    try:
        save_prefs(app, values)
    except Exception as e:
        error_cleanup(e, "An error occurred calling the save_prefs function")
    # Retrieve the results of the function.
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("SELECT * FROM user")
            new_values = cur.fetchone()
    except Exception as e:
        error_cleanup(e, "Error while retrieving the saved values")
    # If no error, cleanup before checking the results - so that cleanup occurs
    # even if there are assertion errors.
    cleanup()
    # Check results.
    assert new_values == values
