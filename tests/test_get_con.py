import sqlite3

from business import get_con


def test_get_con():
    """
    Test the get_con function from the business module.
    """
    # Call the function
    connection = get_con()

    # Check if the connection is not None
    assert connection is not None, "Connection should not be None"

    # Check for specific attributes or methods that a connection object should
    # have.
    assert hasattr(connection, "cursor")
    assert hasattr(connection, "commit")
    assert hasattr(connection, "close")
    # Check the type of the connection - should be sqlite3.Connection.
    assert isinstance(connection, sqlite3.Connection)
