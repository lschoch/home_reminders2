import tkinter as tk

from classes import NotificationsPopup  # noqa: F401
from services2 import UIService


def get_popup_count(root) -> int:
    """
    Counts the number of top level window meeting specified criteria.

    Counts windows of class NotificationsPopup with title 'Notifications'.
    Returns:
        int: The number of top level windows meeting the specified criteria.
    """
    count = 0
    for widget in root.winfo_children():
        if (
            isinstance(widget, NotificationsPopup)
            and widget.title() == "Notifications"
        ):
            count += 1
    return count


def test_remove_notifications_popups():
    """
    Tests the remove_notifications_popups function.

    """
    root = tk.Tk()
    # Create two NotificationsPopup windows to be removed by the function.
    NotificationsPopup(root, title="Notifications")
    NotificationsPopup(root, title="Notifications")
    # Create popups that should not be removed.
    NotificationsPopup(
        root, title="Something else"
    )  # Wrong title for removal.
    tk.Toplevel(root)  # Wrong class for removal.
    # Check that the count of open popup windows is correct.
    assert get_popup_count(root) == 2  # Counts popups eligible for removal.
    # Run the function to remove the popups.
    UIService.remove_notifications_popups(root)
    # Check that no eligible popups remain open.
    assert get_popup_count(root) == 0
    # Check that the two ineligible popups remain open. Note:
    # NotificationsPopup is a subclass of tk.Toplevel.
    count = 0
    for widget in root.winfo_children():
        if isinstance(widget, tk.Toplevel):
            count += 1
    assert count == 2
