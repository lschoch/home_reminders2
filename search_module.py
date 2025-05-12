from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tkinter import ttk


def search_treeview(tree: ttk.Treeview, search_query: str) -> Optional[str]:
    """
    Searches the Treeview for items matching the search query.

    Args:
        tree: The Treeview widget to search.
        search_query (str): The search query string.

    Returns:
        Optional[str]: The ID of the first matching item, or None if no match
        is found.
    """
    query = search_query.lower()
    for item in tree.get_children():
        values = tree.item(item, "values")
        if query in str(values).lower():
            return item  # Return the ID of the matching item
    return None  # Return None if no match is found
