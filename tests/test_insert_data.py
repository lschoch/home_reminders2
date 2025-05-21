import sqlite3
import tkinter as tk

from business import insert_data
from ui_logic import create_tree_widget


def test_insert_data(mocker, get_cursor):
    """
    Test the insert_data function.
    """
    # Mock the treeview widget and insert data from the test database.
    mocker = tk.Tk()
    mocker.tree = create_tree_widget(mocker)
    insert_data(mocker, get_cursor)

    # Print the items in the treeview.
    for i in range(len(mocker.tree.get_children())):
        print(
            f"mocker.tree.get_children()[{i}]:\
                  {mocker.tree.item(mocker.tree.get_children()[i])['values']}"
        )

    # Get data from the database to check against results of the insert_data
    # function: a count of the number of items in the database and the
    # description field of the first item in the database.
    try:
        with sqlite3.connect("./tests/test.db") as con:
            cur = con.cursor()
            cur.execute("SELECT COUNT(*) FROM reminders")
            db_count = cur.fetchone()[0]
            print(f"db_count: {db_count}")
            # Select the first item in the database.
            cur.execute("SELECT * FROM reminders LIMIT 1")
            # Get the description field of the first item in the database.
            description = cur.fetchone()[1]
    except sqlite3.Error as e:
        print(f"Error retrieving data from test database: {e}")
        db_count = 0

    # Add assertions to verify the expected behavior

    # Check if all items in the database have been inserted into the treeview.
    assert len(mocker.tree.get_children()) == db_count

    # Check if the first item inserted in the treeview has the expected text
    assert (
        mocker.tree.item(mocker.tree.get_children()[0])["values"][1]
        == description
    )

    # Check if the first item inserted in the test database has the expected
    # background color (highlighting).
    first_inserted_item = mocker.tree.item(mocker.tree.get_children()[0])
    # Item tags are named as the database index of the item.
    tag_name = first_inserted_item["values"][0]
    print(f"tag_name: {tag_name}")
    # Query the tag configuration to get the background color.
    print(f"tag color: {mocker.tree.tag_configure(tag_name, 'background')}")
    # Check if the tag has the expected background color (yellow).
    assert str(mocker.tree.tag_configure(tag_name, "background")) == "yellow"
