from business import insert_data
from home_reminders import App


def test_insert_data(mocker, get_cursor):
    """
    Test the insert_data function.
    """
    # Mock the treeview widget
    mocker = App()
    # Get the initial number of items in the treeview.
    start_length = len(mocker.tree.get_children())
    insert_data(mocker, get_cursor)
    # Print the items in the treeview.
    for i in range(len(mocker.tree.get_children())):
        print(
            f"mocker.tree.get_children()[{i}]:\
                  {mocker.tree.item(mocker.tree.get_children()[i])['values']}"
        )
    # Add assertions to verify the expected behavior

    # Check if the number of items in the treeview has increased by 2, the
    # of items in the test database.
    assert len(mocker.tree.get_children()) == start_length + 2

    # Check if the first item inserted in the treeview has the expected text
    assert (
        mocker.tree.item(mocker.tree.get_children()[start_length])["values"][1]
        == "testing insert data function"
    )

    # Check if the first item inserted in the test database has the expected
    # background color (highlighted).
    first_inserted_item = mocker.tree.item(
        mocker.tree.get_children()[start_length]
    )
    # tag_name is the database index of the item
    tag_name = first_inserted_item["values"][0]
    print(f"tag_name: {tag_name}")
    # Query the tag configuration for the background color.
    print(f"tag color: {mocker.tree.tag_configure(tag_name, 'background')}")
    # Check if the tag has the expected background color (yellow).
    assert str(mocker.tree.tag_configure(tag_name, "background")) == "yellow"
