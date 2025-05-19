from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Tuple  # noqa: F401

if TYPE_CHECKING:
    import sqlite3

from loguru import logger

from business import (
    categorize_reminders,
    create_message_string,
    delete_item_from_database,
    fetch_reminders,
    get_user_data,
    initialize_user,
    save_database_item,
    save_prefs,
    update_database_item,
)
from classes import InfoMsgBox


class ReminderService:
    @staticmethod
    def get_reminders(self, view_current: bool) -> Optional[sqlite3.Cursor]:  # noqa: PLW0211
        """
        Fetch reminders from the database.

        Args:
            view_current (bool): If True, fetch only pending reminders,
            otherwise, fetch all reminders.

        Returns:
            Optional[sqlite3.Cursor]: List of reminders or None if an error
            occurs.
        """
        try:
            reminders_cursor = fetch_reminders(self, view_current)
            return reminders_cursor if reminders_cursor else None
        except Exception:
            logger.error("Error fetching reminders.")
            InfoMsgBox(self, "Database Error", "Error fetching reminders.")
            return None

    @staticmethod
    def save_reminder(
        self,  # noqa: PLW0211
        values: Tuple[str, str, str, str, str, str],
    ) -> bool:
        """
        Save a new reminder to the database.

        Args:
            values (Tuple): Reminder data to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            save_database_item(self, values)
            return True
        except Exception:
            logger.error("Error saving reminders.")
            InfoMsgBox(self, "Database Error", "Error saving reminders.")
            return False

    @staticmethod
    def update_reminder(
        self,  # noqa: PLW0211
        values: Tuple[str, str, str, str, str, str, int],
    ) -> bool:
        """
        Update an existing reminder in the database.

        Args:
            values (Tuple): Updated reminder data.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            update_database_item(self, values)
            return True
        except Exception:
            logger.error("Error updating reminders.")
            InfoMsgBox(self, "Database Error", "Error updating reminders.")
            return False

    @staticmethod
    def delete_reminder(self, reminder_id: int) -> bool:  # noqa: PLW0211
        """
        Delete a reminder from the database.

        Args:
            reminder_id (int): ID of the reminder to delete.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            delete_item_from_database(self, reminder_id)
            return True
        except Exception:
            logger.error("Error deleting reminders.")
            InfoMsgBox(self, "Database Error", "Error deleting reminders.")
            return False

    @staticmethod
    def get_user_preferences(self) -> Optional[Tuple]:  # noqa: PLW0211
        """
        Fetch user preferences from the database.

        Returns:
            Optional[Tuple]: User preferences or None if an error occurs.
        """
        try:
            user_data = get_user_data(self)
            return user_data.fetchone() if user_data else None
        except Exception:
            logger.error("Error fetching user preferences.")
            InfoMsgBox(
                self, "Database Error", "Error fetching user preferences."
            )
            return None

    @staticmethod
    def save_user_preferences(self, values: Tuple) -> bool:  # noqa: PLW0211
        """
        Save user preferences to the database.

        Args:
            values (Tuple): User preferences to save.

        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            save_prefs(self, values)
            return True
        except Exception:
            logger.error("Error saving user preferences.")
            InfoMsgBox(
                self, "Database Error", "Error saving user preferences."
            )
            return False

    @staticmethod
    def get_notifications(self) -> str:  # noqa: PLW0211
        """
        Generate a string of notifications based on reminders and user
        preferences.

        Returns:
            str: Notifications message.
        """
        initialize_user(self)
        user_data = ReminderService.get_user_preferences(self)
        if not user_data:
            return ""

        reminders = ReminderService.get_reminders(self, view_current=False)
        if not reminders:
            return ""

        categorized_reminders = categorize_reminders(reminders)
        return create_message_string(user_data, categorized_reminders)

    @staticmethod
    def validate_phone_number(self, num: str) -> bool:  # noqa: PLW0211
        """
        Checks validity of user phone number.

        Args:
            (str): Phone number entered by user.
        Returns:
            (bool): True if phone number is valid, False otherwise.
        """
        if not num.isnumeric() or len(num) > 10 or len(num) < 10:
            InfoMsgBox(
                self,
                "Notifications",
                "Phone number must be a ten digit numeric.",
                x_offset=100,
                y_offset=15,
            )
            return False
        return True
