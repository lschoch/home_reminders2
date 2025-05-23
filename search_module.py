from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from tkinter import ttk


def search_treeview(tree: ttk.Treeview, search_query: str) -> Optional[list]:
    """
    Searches the Treeview for items matching the search query.

    Args:
        tree: The Treeview widget to search.
        search_query (str): The search query string.

    Returns:
        Optional[str]: List of matching item ID's, or None if no match
        is found.
    """
    query = search_query.lower()
    matching_items = []
    for item in tree.get_children():
        values = tree.item(item, "values")
        if query in str(values).lower():
            matching_items.append(item)
    if matching_items:
        return matching_items
    return None  # Return None if no matches are found
