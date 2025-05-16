from __future__ import annotations

import tkinter as tk
from typing import TYPE_CHECKING, Any, Optional, Tuple  # noqa: F401

from classes import NofificationsPopup


class UIService:
    @staticmethod
    def remove_notifications_popups(self) -> Any:  # noqa: PLW0211
        """
        Removes any pre-existing notifications popups that haven't been closed.

        Args:
            none
        Returns:
            None
        """
        for widget in self.winfo_children():
            if (
                isinstance(widget, tk.Toplevel)
                and widget.title() == "Notifications"
            ):
                widget.destroy()

    def create_notifications_popup(self, messages: str) -> Any:
        """
        Creates a Notifications Popup window.

        Displays a bulleted list of reminder notifications, categorized by due
        date.
        Args:
            messages (str): The string of reminder notifications to be
            displayed.
        Returns:
            None.
        """
        if messages == "No notifications.":
            notifications_win = NofificationsPopup(
                self,
                title="Notifications",
                message="No notifications at this time.",
                x_offset=310,
                y_offset=400,
            )
        else:
            # Remove the trailing \n from messages.
            messages = messages[:-1]
            # Create the window.
            notifications_win = NofificationsPopup(
                self,
                title="Notifications",
                message="",
                x_offset=310,
                y_offset=400,
            )
            # Add highlighting to messages.
            message_list = messages.split("\n")
            line_num = 1
            for ndx, msg in enumerate(message_list):
                line_num = ndx + 1  # ndx starts at 0, lin_num starts at 1
                if msg.startswith("\u2022 Past due"):
                    notifications_win.txt.insert("end", msg + "\n")
                    indx_start = str(line_num) + ".0"
                    indx_end = str(line_num + 1) + ".0"
                    notifications_win.txt.tag_add(
                        "yellow", indx_start, indx_end
                    )
                    notifications_win.txt.tag_config(
                        "yellow", background="yellow"
                    )
                elif msg.startswith("\u2022 Due today"):
                    notifications_win.txt.insert("end", msg + "\n")
                    indx_start = str(line_num) + ".0"
                    indx_end = str(line_num + 1) + ".0"
                    notifications_win.txt.tag_add("lime", indx_start, indx_end)
                    notifications_win.txt.tag_config("lime", background="lime")
                else:
                    notifications_win.txt.insert("end", msg + "\n")
