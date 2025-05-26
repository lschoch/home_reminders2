import sqlite3

from business import get_con


def test_get_con():
    """
    Test the get_con function from the business module.
    """
    # Call the function
    connection = get_con(db="test.db")

    # Check if the connection is established and not None.
    # This assumes that get_con returns a valid sqlite3.Connection object.
    assert connection is not None

    # Check for specific attributes or methods that a connection object should
    # have.
    assert hasattr(connection, "cursor")
    assert hasattr(connection, "commit")
    assert hasattr(connection, "close")
    # Check the type of the connection - should be sqlite3.Connection.
    assert isinstance(connection, sqlite3.Connection)

    # Retrieve the cursor from the connection and check if it is valid.
    cursor = connection.cursor()
    assert cursor is not None
    assert isinstance(cursor, sqlite3.Cursor)

    # Clean up by closing the connection.
    connection.close()
