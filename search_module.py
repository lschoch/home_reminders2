import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional  # noqa: F401


def search_treeview(
    tree: ttk.Treeview,
    search_var: tk.StringVar,
    remove_toplevels: Callable[[], None],
):
    """
    Searches the Treeview for items matching the search query.

    Args:
        tree: The Treeview widget to search.
        search_var (str): The StringVar containing the search query.
        remove_toplevels (callable): A callback function to remove any existing
         toplevel windows.
    """
    query = search_var.get().lower()
    for item in tree.get_children():
        values = tree.item(item, "values")
        if query in str(values).lower():
            tree.selection_set(item)
            remove_toplevels()  # Call the callback to remove toplevels
            # Scroll to and set focus on the item found.
            tree.see(item)
            tree.focus(item)
            break
