import sqlite3
import tkinter as tk
from datetime import date, datetime

from loguru import logger

from business import insert_data
from ui_logic import create_tree_widget


def test_insert_data(get_cursor):
    """
    Test the insert_data function.
    """
    # Mock the app and create treeview widget.
    app = tk.Tk()
    app.tree = create_tree_widget(app)

    # Log the items in the treeview.
    for i in range(len(app.tree.get_children())):
        logger.info(
            f"app.tree.get_children()[{i}]:\
                  {app.tree.item(app.tree.get_children()[i])['values']}"
        )

    # Get data from the database to check against results of the insert_data
    # function.
    try:
        with sqlite3.connect("./tests/test.db") as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM reminders")
            db_count = cur.fetchone()[0]
            logger.info(f"db_count: {db_count}")
            # Select the first item in the database.
            first_reminder = cur.execute(
                "SELECT * FROM reminders LIMIT 1"
            ).fetchone()
            # Get the description and next date fields of the first item in the
            # database.
            description = first_reminder[1]
            next_date = first_reminder[5]
    except sqlite3.Error as e:
        logger.info(f"Error retrieving data from test database: {e}")
        db_count = 0

    # Get expected highlight color of the item in the database based on next
    # date field.
    next_date_datetime = datetime.strptime(next_date, "%Y-%m-%d").date()
    if next_date_datetime < date.today():
        expected_color = "yellow"
    elif next_date_datetime == date.today():
        expected_color = "lime"
    else:
        expected_color = "white"

    # Check that treeview is empty at this stage.
    assert len(app.tree.get_children()) == 0

    # Insert get_cursor data into the mock treeview.
    insert_data(app, get_cursor)

    # Verify the expected behavior of the insert_data function:

    # Check if all items in the database have been inserted into the treeview.
    assert len(app.tree.get_children()) == db_count
    # Check if the first item inserted in the treeview has the expected text
    assert (
        app.tree.item(app.tree.get_children()[0])["values"][1] == description
    )
    # Check if the first item inserted in the test database has the expected
    # background color (highlighting).
    first_inserted_item = app.tree.item(app.tree.get_children()[0])
    # Item tags are named as the database index of the item.
    tag_name = first_inserted_item["values"][0]
    logger.info(f"tag_name: {tag_name}")
    # Query the tag configuration to get the background color.
    logger.info(f"tag color: {app.tree.tag_configure(tag_name, 'background')}")
    # Check if the tag has the expected background color.
    assert (
        str(app.tree.tag_configure(tag_name, "background")) == expected_color
    )
