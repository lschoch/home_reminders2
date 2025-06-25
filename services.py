from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Tuple  # noqa: F401

if TYPE_CHECKING:
    import sqlite3

import datetime
import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from loguru import logger

from business import (
    fetch_reminders,
    get_con,
    get_user_data,
    save_database_item,
    save_prefs,
    update_database_item,
)
from classes import InfoMsgBox

SCOPES = ["https://www.googleapis.com/auth/calendar"]


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
            with get_con() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    DELETE FROM reminders
                    WHERE id = ?""",
                    (reminder_id,),
                )
                con.commit()
            return True
        except Exception as e:
            logger.error(f"Error deleting reminder: {e}")
            InfoMsgBox(self, "Database Error", "Error deleting reminder.")
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

    @staticmethod
    def create_calendar_event(self, reminder_id: int) -> bool:  # noqa: PLW0211
        """
        Record a reminder as an event on the calendar.

        Args:
            reminder_id (int): ID of the reminder to schedule.

        Returns:
            bool: True if successful, False otherwise.
        """
        # Load credentials.
        try:
            creds = None

            if os.path.exists("token.pickle"):
                with open("token.pickle", "rb") as token:
                    creds = pickle.load(token)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        "../credentials.json", SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                with open("token.pickle", "wb") as token:
                    pickle.dump(creds, token)
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            InfoMsgBox(self, "Credentials Error", "Error loading credentials.")
            return False
        # Create the calendar service.
        try:
            service = build("calendar", "v3", credentials=creds)
        except Exception as e:
            logger.error(f"Error creating calendar service: {e}")
            InfoMsgBox(
                self,
                "Calendar Service Error",
                "Error creating calendar service.",
            )
            return False
        # Fetch the reminder details from the database.
        with get_con() as con:
            cur = con.cursor()
            cur.execute(
                """
                SELECT *
                FROM reminders
                WHERE id = ?
                """,
                (reminder_id,),
            )
            reminder = cur.fetchone()

        if not reminder:
            logger.error("Reminder not found.")
            InfoMsgBox(self, "Reminder Error", "Reminder not found.")
            return False

        # Check if the reminder is already scheduled.
        start_date = reminder[4]  # reminder[4] is the date last.
        end_datetime = datetime.datetime.strptime(
            start_date, "%Y-%m-%d"
        ) + datetime.timedelta(days=1)
        end_date = end_datetime.strftime("%Y-%m-%d")
        logger.info(f"Getting events for {start_date}")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=f"{start_date}T00:00:00Z",
                timeMax=f"{end_date}T00:00:00Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        # Check if the event already exists.
        if events:
            for event in events:
                if (
                    reminder[1] in event["summary"]
                ):  # reminder[1] is the description.
                    logger.info("Event already exists.")
                    InfoMsgBox(
                        self,
                        "Create Event",
                        "Event already exists in the calendar.",
                    )
                    return False

        # Create the event.
        event = {
            "summary": f"HR: {reminder[1]}",  # reminder[1] is the description.
            "description": reminder[6],  # reminder[6] is the note
            "start": {
                "date": reminder[4],  # reminder[4] is the date last.
                "timeZone": "America/New_York",
            },
            "end": {
                "date": reminder[4],  # reminder[4] is the date last.
                "timeZone": "America/New_York",
            },
        }
        # Insert the event into the calendar.
        try:
            created_event = (
                service.events()
                .insert(calendarId="primary", body=event)
                .execute()
            )
            logger.info(f"Event created: {created_event['id']}")
            return True
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            InfoMsgBox(self, "Event Creation Error", "Error creating event.")
            return False
        # If the event is created successfully, return True.
        # If there is an error, return False.
        # Note: The function currently does not handle the case where the event
        # already exists. You may want to add logic to check for existing
        # events and update them if necessary.
        # This can be done by checking the calendar for existing events with
        # the same summary and date.
        # If an event with the same summary and date already exists, you can
        # either skip creating the new event or update the existing event with
        # the new details.
        # This can be done by using the event ID to update the existing event.
        # You can also add logic to handle conflicts, such as asking the user
        # if they want to overwrite the existing event or create a new one with
        # a different summary or date.
