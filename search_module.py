from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

from classes import InfoMsgBox

if TYPE_CHECKING:
    import tkinter as tk
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


def get_matching_items(tree, search_var):
    search_query = search_var.get()
    return search_treeview(tree, search_query)


def next_found(self, search_var: tk.StringVar) -> Any:
    next_found.counter += 1
    matching_items = get_matching_items(self.tree, search_var)
    if matching_items:
        # Perform UI operations for the matching items
        iterator_next = iter(matching_items)
        if next_found.counter > len(matching_items):
            self.tree.selection_set(matching_items[0])
            self.tree.see(matching_items[0])
            next_found.counter = 1
        try:
            for _ in range(next_found.counter):
                matching_item = next(iterator_next)
            self.tree.selection_set(matching_item)
            self.tree.see(matching_item)
            return
        except StopIteration:
            logger.info("No more items to iterate over.")
            return
    else:
        # Optionally, show a message if no match is found
        InfoMsgBox(self, "Search", "No matching item found.")


next_found.counter = 0
