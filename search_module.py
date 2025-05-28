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


def get_matching_items(
    tree: ttk.Treeview, search_var: tk.StringVar
) -> Optional[list]:
    """
    Gets the list of items in a tree matching a search term.

    Args:
        tree (ttk.Treeview): The tree to be searched.
        search_var (tk.StringVar): The search term.
    Returns:
        Optional[list]: The list of items in the tree matching the search term.
    """
    search_query = search_var.get()
    return search_treeview(tree, search_query)


def next_found(self, search_var: tk.StringVar) -> Any:
    """
    Selects the next item in a list of items from a tree matching a search term

    Args:
        search_var (tk.StringVar): The search term used to select the list of
        matching items.
    Returns:
        None

    """
    # If search field is empty, abort search and display message .
    if not search_var.get():
        InfoMsgBox(self, "Search", "Please enter a search term.")
        return
    matching_items = get_matching_items(self.tree, search_var)
    if matching_items:
        # Sequential selection of found items using the find_next button.
        try:
            matching_item = matching_items[next_found.counter]  # type:ignore
            self.tree.selection_set(matching_item)
            self.tree.see(matching_item)
            # Increment counter by one to move to next reminder. Reset counter
            # to start over after the last reminder is selected.
            next_found.counter = (  # type:ignore
                0
                if next_found.counter == len(matching_items) - 1  # type:ignore
                else next_found.counter + 1  # type:ignore
            )
        except Exception as e:
            logger.error(
                f"An error occurred while selecting matching items: {e}."
            )
            InfoMsgBox(
                self,
                "Error",
                "An error occurred while selecting matching items.",
            )
            return
    else:
        # Optionally, show a message if no match is found
        InfoMsgBox(self, "Search", "No matching item found.")


next_found.counter = 0  # type:ignore
