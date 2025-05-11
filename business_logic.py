from __future__ import annotations

import importlib
import os
import shutil
import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk
from typing import Any, Optional, Tuple  # noqa: F401

from dateutil.relativedelta import relativedelta  # type: ignore

# from icecream import ic  # noqa: F401
from tkcalendar import Calendar  # type: ignore

from classes import (
    InfoMsgBox,
    YesNoMsgBox,
)


def on_treeview_selection_changed(self, event) -> Any:
    """
    Function to manage row selection in treeview. Creates window to edit/delete
    the selected item. Populates the window with the selected item's data. Does
    not return anything.
    """
    # abort if the selection change was after a refresh
    if self.refreshed:
        self.refreshed = False
        return
    selected_item = self.tree.focus()
    # Import ui_logic using importlib.import_module(). This will avoid circular
    # import conflict with business_logic.
    module = importlib.import_module("ui_logic")
    # Create window to edit the selected item. Populate with the selected item
    # data.
    module.create_edit_window(self, selected_item)


def insert_data(self, data: Optional[sqlite3.Cursor]) -> Any:
    """
    Function to insert data into the treeview. It takes a cursor object
    as a parameter and iterates through the data, inserting each item into
    the treeview. It uses the first item in each tuple as a tag to color
    (highlight) the row based on the date_next value.
    """
    if data:
        for item in data:
            self.tree.insert("", tk.END, values=item, tags=item[0])
            if item[5] is None:
                self.tree.tag_configure(item[0], background="#ececec")
            else:
                dat_nxt = datetime.strptime(item[5], "%Y-%m-%d").date()
                if dat_nxt < date.today():
                    self.tree.tag_configure(item[0], background="yellow")
                elif dat_nxt == date.today():
                    self.tree.tag_configure(item[0], background="lime")
                else:
                    self.tree.tag_configure(item[0], background="white")
            # self.tree.tag_configure(item[0], font=("Helvetica", 13))


def get_date(date_last_entry: date, top) -> Any:
    """
    Function to select a date from the calendar. Takes date_last_entry and top
    as paramteters. Default selection is the date_last_entry provided as
    parameter. Sets date_last_entry to the clicked date.
    """
    # destroy calendar if it already exists (prevents multiple overlying
    # calendars from repeatedly clicking the entry)
    for child in top.winfo_children():
        if isinstance(child, tk.Toplevel):
            child.destroy()

    # function to set date_last_entry from calendar click
    def on_cal_selection_changed(event):
        date_last_entry.delete(0, tk.END)
        date_last_entry.insert(0, cal.selection_get())
        top2.wm_overrideredirect(False)
        top2.destroy()

    # create a toplevel for the calendar
    top2 = tk.Toplevel(top)

    # remove title bar
    top2.wm_overrideredirect(True)

    top2.configure(background="#cacaca")
    x = top.winfo_x()
    y = top.winfo_y()
    top2.geometry("+%d+%d" % (x + 187, y - 25))

    # keep calendar in front of it's parent window
    top2.wm_transient(top)

    cal = Calendar(
        top2,
        font="Arial 14",
        selectmode="day",
        cursor="arrow",
        locale="en_US",
        date_pattern="yyyy/mm/dd",
        showweeknumbers="False",
        foreground="black",
        background="#cacaca",
        headersbackground="#dbdbdb",
        weekendbackground="white",
        othermonthwebackground="#ececec",
        selectforeground="red",
        selectbackground="#dbdbdb",
    )

    # if date_last_entry is not empty, set calendar to date_last_entry
    if top.date_last_entry.get():
        cal.selection_set(top.date_last_entry.get())
    cal.grid(row=0, column=0)

    ttk.Button(top2, text="cancel", width=6, command=top2.destroy).grid(
        row=1, column=0
    )

    # bind CalendarSelected event to function that sets date_last_entry
    cal.bind("<<CalendarSelected>>", on_cal_selection_changed)


def refresh(self) -> Any:
    """Function to update treeview and labels after a change to the database"""
    # Fetch fresh set of reminders and insert into treeview.
    refreshed_data = fetch_reminders(self)
    for item in self.tree.get_children():
        self.tree.delete(item)
    insert_data(self, refreshed_data)
    self.refreshed = True
    # Update label messages.
    if self.view_current:
        view_msg = (
            "Viewing pending items only - select an item to edit or delete."
        )
    else:
        view_msg = "Viewing all items - select an item to edit or delete."
    self.view_lbl_msg.set(view_msg)
    self.view_lbl.config(background="#ececec")


def date_next_calc(top) -> str:
    """
    Function to calculate next date for an item based on frequency and period,
    """
    date_last = top.date_last_entry.get()
    frequency = int(top.frequency_entry.get())
    period = top.period_combobox.get()
    match period:
        case "":
            date_next = ""
        case "one-time":
            date_next = (
                datetime.strptime(date_last, "%Y-%m-%d")
                .date()
                .strftime("%Y-%m-%d")
            )
        case "days":
            date_next = (
                datetime.strptime(date_last, "%Y-%m-%d").date()
                + timedelta(days=frequency)
            ).strftime("%Y-%m-%d")
        case "weeks":
            date_next = (
                datetime.strptime(date_last, "%Y-%m-%d").date()
                + timedelta(weeks=frequency)
            ).strftime("%Y-%m-%d")
        case "months":
            date_next = (
                datetime.strptime(date_last, "%Y-%m-%d").date()
                + relativedelta(months=frequency)
            ).strftime("%Y-%m-%d")
        case "years":
            date_next = (
                datetime.strptime(date_last, "%Y-%m-%d").date()
                + relativedelta(years=frequency)
            ).strftime("%Y-%m-%d")
    return date_next


def get_con() -> sqlite3.Connection:
    """Function to create a connection to the SQLite database. It checks if the
    path to the database exists, and if not, creates the necessary directories.
    It returns a connection object to the database file located in the "Home
    Reminders" directory within the Application Support directory of the user's
    home directory.
    """
    dir_path = os.path.join(appsupportdir(), "Home Reminders")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    file_path = os.path.join(dir_path, "home_reminders.db")
    return sqlite3.connect(file_path)


def appsupportdir() -> str | os.PathLike:
    """
    Function to get the Application Support directory based on the user's
    operating system. It checks for the existence of the Application Support
    directory in macOS and Linux, and the AppData directory in Windows. If
    none of these directories exist, it returns the user's home directory.
    """
    windows = r"%APPDATA%"
    windows = os.path.expandvars(windows)
    if "APPDATA" not in windows:
        return windows

    user_directory = os.path.expanduser("~")

    macos = os.path.join(user_directory, "Library", "Application Support")
    if os.path.exists(macos):
        return macos

    linux = os.path.join(user_directory, ".local", "share")
    if os.path.exists(linux):
        return linux

    return user_directory


def initialize_user(self) -> Any:
    """
    Function to initialize the user table if it is empty.

    Args:
        none
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            empty_check = cur.execute("SELECT COUNT(*) FROM user").fetchall()
            if empty_check[0][0] == 0:  # phone number is 0, initialize
                values = (0, 0, 0, "1970-01-01")
                cur.execute(
                    """
                    INSERT INTO user (
                        week_before,
                        day_before,
                        day_of,
                        last_notification_date)
                        VALUES (?, ?, ?, ?)""",
                    values,
                )
                con.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to update the database.")


def save_prefs(self, values) -> Any:
    """
    Saves user preferences to the database.

    Args:
        values (tuple): 5 tuple containing user preferences to be saved.
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM user")
            # Write new user data to user table.
            cur.execute(
                """INSERT INTO user (
                phone_number,
                week_before,
                day_before,
                day_of,
                last_notification_date) VALUES(?, ?, ?, ?, ?)""",
                values,
            )
            con.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to update the database.")
    # If there was a pre-existing phone number, there was a pre-existing user.
    if values[0]:
        InfoMsgBox(
            self,
            "Notifications",
            "Your data has been saved.",
            x_offset=100,
            y_offset=15,
        )
    else:
        InfoMsgBox(
            self,
            "Notifications",
            "You will now start receiving text notifications.",
            x_offset=100,
            y_offset=15,
        )


def notifications_popup(self) -> Any:  # noqa: C901, PLR0912, PLR0915
    """
    Checks for reminder notifications. Creates a notifications popup if needed.

    Checks every four hours for items that are past due, due today, due
    tomorrow, or due in 7 days, depending on user preferences. Also removes any
    pre-existing notifications popups to prevent multiple popups from
    accumulating.
    Args:
        none.
    Returns:
        None
    """
    # Initialize user table in case it's empty.
    initialize_user(self)
    # Remove any pre-existing notifications popups that havent' been closed by
    # the user.
    module = importlib.import_module("ui_logic")
    module.remove_notifications_popups(self)
    # Fetch reminders if user has opted to receive notifiications.
    user_data = get_user_data(self)
    # user_data[0] is phone number. If present, user has opted to receive
    # notifications.
    if user_data[0]:
        # Fetch all reminders. If view_current is set to True, temporarily
        # reset it to False so that all reminders will be retrieved instead of
        # just the pending reminders.
        if self.view_current:
            self.view_current = False
            reminders = fetch_reminders(self)
            # Reset view_current.
            self.view_current = True
        else:
            reminders = fetch_reminders(self)
    else:
        reminders = None
    # Categorize reminders, if any, by due date.
    if reminders:
        reminders_by_category = categorize_reminders(reminders)
        # Create string of notifications messages.
        messages = create_message_string(user_data, reminders_by_category)
        # If there are any messages, create a notifications popup.
        if messages:
            module = importlib.import_module("ui_logic")
            module.create_notifications_popup(self, messages)

    # Check for notifications every 4 hours.
    self.after(14400000, notifications_popup, self)


def date_check(self) -> Any:
    """
    On date change, updates the today is label and refreshes treeview.

    Calls itself every second to monitor for date change. On date change,
    updates the today is label and refreshes the treeview to keep highlighting
    accurate. This is needed because the app is meant to remain open for
    extended periods.
    Args:
        none
    Returns:
        None
    """
    # Check if the date has changed.
    if self.todays_date_var.get() != datetime.now().strftime("%Y-%m-%d"):
        # update the label to show today's date
        self.todays_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.today_is_lbl.config(
            text=f"Today is {self.todays_date_var.get()}",
        )
    # Check every second.
    self.after(1000, date_check, self)


def create_database(self) -> Any:
    """
    Function to create database if it does not exist. Does not return anything.

    Args:
        none
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            # Create user table to store user phone number and notifications
            # preferences, if it doesn't exist.
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user(
                    phone_number TEXT,
                    week_before INT,
                    day_before INT,
                    day_of INT,
                    last_notification_date TEXT)
            """)
            # Create reminders table to store reminders, if it doesn't exist
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reminders(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT,
                    frequency TEXT,
                    period TEXT,
                    date_last TEXT,
                    date_next TEXT,
                    note TEXT)
            """)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to create the database.")


def fetch_reminders(self) -> Optional[sqlite3.Cursor]:
    """
    Retrieves reminders from the database.

    Fetches either the pending reminders or all reminders depending on the
    value of the attribute view_current.
    Args:
        none
    Returns:
        Optional[sqlite3.Cursor]: Cursor object containging the retrieved
        reminder items.
    """
    # connect to database and create cursor
    try:
        with get_con() as con:
            cur = con.cursor()
            # retrieve and return data depending on the current view
            if self.view_current:
                return cur.execute("""
                    SELECT * FROM reminders
                    WHERE date_next >= DATE('now', 'localtime')
                                        OR date_next IS NULL
                    ORDER BY date_next ASC, description ASC
                """)
            else:
                return cur.execute("""
                    SELECT * FROM reminders
                    ORDER BY date_next ASC, description ASC
                """)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    return None


def validate_inputs(self, top, id: int | None = None) -> bool:
    """
    Function to validate inputs for new and edited reminder items.
    Returns True if inputs are valid, False otherwise.
    """
    # description is required
    description = top.description_entry.get()
    if not description:
        InfoMsgBox(
            self,
            "Invalid Input",
            "Description cannot be blank.",
        )
        description.focus_set()
        return False
    # Fetch all reminders. If view_current is set to True, temporarily reset
    # it to False so that all reminders will be retrieved instead of just the
    # pending reminders.
    if self.view_current:
        self.view_current = False
        data = fetch_reminders(self)
        # Reset view_current.
        self.view_current = True
    else:
        data = fetch_reminders(self)
    items = data.fetchall()
    # If updating an existing item, get the pre-edit description. Item[0] is
    # the id in the database, item[1] is the description in the database.
    original_description = None
    if id:
        for item in items:
            if item[0] == id:
                original_description = item[1]
    # Check for duplicate description.
    for item in items:
        if item[1] == description:
            # It's not a duplicate if updating an existing item, and not
            # changing the description.
            if original_description:
                break
            InfoMsgBox(
                self,
                "Duplicate Description",
                "There is already an entry with this description."
                + " Try again.",
            )
            # if updating an existing item, reset original description
            if id == item[0]:
                description.delete(0, tk.END)
                description.insert(0, original_description)
                description.focus_set()
            return False
    # frequency is required and must be an integer
    frequency = top.frequency_entry.get()
    if not frequency or not int(frequency):
        InfoMsgBox(
            self,
            "Invalid Input",
            "Please enter frequency as integer.",
        )
        top.frequency_entry.focus_set()
        return False
    # period and date_last_entry are required
    if not top.period_combobox.get():
        InfoMsgBox(
            self,
            "Invalid Input",
            "Please select the period.",
        )
        top.period_combobox.focus_set()
        return False
    if not top.date_last_entry.get():
        InfoMsgBox(
            self,
            "Invalid Input",
            "Please select the last date.",
        )
        top.date_last_entry.focus_set()
        return False
    return True


def delete_user_data(self) -> Any:
    """
    Function to delete user data from the user table.

    Args:
        none
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute("DELETE FROM user")
            con.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(
            self, "Error", "Failed to delete user data from the database."
        )


def opt_in(self) -> Any:
    """
    Creates dialog giving user the option to start receiving notifications.
    Args:
        none
    Returns:
        None
    """
    # The following import was deferred to avoid circular imports.
    from ui_logic import create_preferences_window

    # initialize user table if empty
    initialize_user(self)
    phone_number = get_user_data(self)[0]
    if not phone_number:
        response = YesNoMsgBox(
            self,
            title="Notifications",
            message="Would you like to to be notified by text "
            + "when your items are coming due?",
            x_offset=3,
            y_offset=5,
        )
        # if user opts to receive notifications, get user data
        if response.get_response():
            create_preferences_window(self)
        else:
            InfoMsgBox(
                self,
                "Notifications",
                "You have opted out of text notifications."
                + " Texts will no longer be sent.",
                x_offset=3,
                y_offset=5,
            )
            # delete user data if user opts out
            delete_user_data(self)
    else:
        response1 = YesNoMsgBox(
            self,
            title="Notifications",
            message="You are already receiving text"
            + " notifications? Do want to continue receiving them?",
            x_offset=3,
            y_offset=5,
        )
        if not response1.get_response():
            InfoMsgBox(
                self,
                "Notifications",
                "You have opted out of text notifications."
                + " Texts will no longer be sent.",
                x_offset=3,
                y_offset=5,
            )
            # delete user data if user opts out
            delete_user_data(self)
        elif response1.get_response():
            response2 = YesNoMsgBox(
                self,
                title="Notifications",
                message="""Do you want to change your notification
                    phone number or notification frequency?""",
                x_offset=3,
                y_offset=5,
            )
            if response2.get_response():
                create_preferences_window(self)


def opt_out(self) -> Any:
    """
    Creates dialog giving user the option to opt out of notifications.

    Args:
        none
    Returns:
        None
    """
    initialize_user(self)
    phone_number = get_user_data(self)[0]
    if phone_number:
        response = YesNoMsgBox(
            self,
            title="Notifications",
            message="""Do you want to stop receiving
                text notifications?""",
            x_offset=3,
            y_offset=5,
        )
        if response.get_response():
            InfoMsgBox(
                self,
                "Notifications",
                "You have opted out of text notifications."
                + " Texts will no longer be sent.",
                x_offset=3,
                y_offset=5,
            )
            delete_user_data(self)
    else:
        InfoMsgBox(
            self,
            "Notifications",
            "You are not currently receiving text notifications. "
            + "Click opt-in to start.",
            x_offset=3,
            y_offset=5,
        )


def preferences(self) -> Any:
    """
    Creates dialog giving user the option to modify notification preferences.

    Args:
        none
    Returns:
        None
    """
    # The following import was deferred to avoid circular imports.
    from ui_logic import create_preferences_window

    initialize_user(self)
    # check to see if user has a phone number; i.e., already receiving
    # notifications
    phone_number = get_user_data(self)[0]
    if phone_number:
        create_preferences_window(self)
    else:
        InfoMsgBox(
            self,
            "Notifications",
            "You are not currently receiving text notifications. "
            + "Click opt-in to start.",
            x_offset=3,
            y_offset=5,
        )


def view_pending(self) -> Any:
    """
    Changes the treeview to list only items due today or in the future.

    Args:
        none
    Returns:
        None
    """
    self.view_current = True
    data = fetch_reminders(self)
    insert_data(self, data)
    refresh(self)
    module = importlib.import_module("ui_logic")
    module.remove_toplevels(self)
    self.refreshed = True
    self.tree.focus()


def view_all(self) -> Any:
    """
    Changes the treeview to list all items, including thise that are past due.

    Args:
        none
    Returns:
        None
    """
    self.view_current = False
    data = fetch_reminders(self)
    insert_data(self, data)
    refresh(self)
    module = importlib.import_module("ui_logic")
    module.remove_toplevels(self)
    self.refreshed = True
    self.focus_set()
    self.tree.focus_set()


def get_db_paths() -> tuple[str | os.PathLike, str | os.PathLike]:
    """
    Gets paths to database and database backup.

    Args:
        none
    Returns:
        (tuple[str | os.PathLike, str | os.PathLike]):  A 2 tuple containing
        the path to the database and the path to the database backup.
    """
    db_base_path = os.path.join(appsupportdir(), "Home Reminders")
    if not os.path.exists(db_base_path):
        os.makedirs(db_base_path)
    db_path = os.path.join(db_base_path, "home_reminders.db")
    db_bak_path = os.path.join(db_base_path, "home_reminders.bak")
    return (db_path, db_bak_path)


def backup(self) -> Any:
    """
    Creates dialog giving user the option to create a database backup.

    Args:
        none
    Returns:
        None
    """
    answer = YesNoMsgBox(
        self,
        "Backup",
        "The current backup will be overwritten. Are you sure?",
        x_offset=3,
        y_offset=5,
    )
    if answer.get_response():
        paths = get_db_paths()
        db_path = paths[0]
        db_bak_path = paths[1]
        shutil.copy2(db_path, db_bak_path)
        InfoMsgBox(
            self,
            "Backup",
            "Backup completed.",
            x_offset=3,
            y_offset=5,
        )
    else:
        return


def restore(self) -> Any:
    """
    Creates dialog giving user the option to restore the database.

    Args:
        none
    Returns:
        None
    """
    answer = YesNoMsgBox(
        self,
        "Restore",
        "All current data will be overwritten. Are you sure?",
        x_offset=3,
        y_offset=5,
    )
    if answer.get_response():
        paths = get_db_paths()
        db_path = paths[0]
        db_bak_path = paths[1]
        shutil.copy2(db_bak_path, db_path)
        refresh(self)
        InfoMsgBox(
            self,
            "Restore",
            "Data restored.",
            x_offset=3,
            y_offset=5,
        )
    else:
        return


def delete_all(self) -> Any:
    """
    Creates dialog giving user the option to delete the database.

    Args:
        none
    Returns:
        None
    """
    answer = YesNoMsgBox(
        self,
        "Delete All",
        "This will delete all data. Are you sure?",
        x_offset=3,
        y_offset=5,
    )
    if answer.get_response():
        try:
            with get_con() as con:
                cur = con.cursor()
                cur.execute("DELETE FROM reminders")
                con.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            InfoMsgBox(
                self, "Error", "Failed to delete user data from the database."
            )
        refresh(self)
        InfoMsgBox(
            self,
            "Delete All",
            "Data has been deleted.",
            x_offset=3,
            y_offset=5,
        )
    else:
        return


def get_user_data(self) -> Any:
    """
    Gets user preferences from the user table.

    Args:
        none
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            return cur.execute("SELECT * FROM user").fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to get user_data from the database.")


def delete_item_from_database(self, id: int) -> Any:
    """
    Deletes a reminder item from the database.

    Args:
        id (int): The id of the item to be deleted.
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute(
                """
                DELETE FROM reminders
                WHERE id = ?""",
                (id,),
            )
            con.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to update the database.")


def save_database_item(
    self, values: Tuple[str, str, str, str, str, str]
) -> Any:
    """
    Saves a new reminder item to the database.

    Args:
        values (tuple):  A 6 tuple containing reminder item data.
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            # insert data into database
            cur.execute(
                """
                INSERT INTO reminders (
                    description,
                    frequency,
                    period,
                    date_last,
                    date_next,
                    note)
                VALUES (?, ?, ?, ?, ?, ?)""",
                values,
            )
            con.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(
            self, "Error", "Failed to save new reminder item to the database."
        )
    refresh(self)
    return None


def update_database_item(
    self, values: Tuple[str, str, str, str, str, str, int]
) -> Any:
    """
    Updates selected reminder item in the database.

    Args:
        values (tuple): a 7 tuple containing the edited data of the selected
        reminder item, the last element of which is the reminder item id.
    Returns:
        None
    """
    try:
        with get_con() as con:
            cur = con.cursor()
            cur.execute(
                """
                UPDATE reminders
                SET (
                description, frequency, period, date_last, date_next, note)
                = (?, ?, ?, ?, ?, ?)
                WHERE id = ? """,
                (values),
            )
            con.commit()
            refresh(self)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(
            self,
            "Error",
            "Failed to update selected reminder item in the database.",
        )
    refresh(self)
    return None


def categorize_reminders(
    reminders: Optional[sqlite3.Cursor],
) -> Tuple[list[str], list[str], list[str], list[str]]:
    """
    Creates lists of notification reminders categorized by due date.

    Args:
        reminders (Optional[sqlite3.Cursor]): Cursor object containing the
        remninder items to be categorized.
    Returns:
        Tuple[list[str], list[str], list[str], list[str]]: A tuple containing 4
        lists: past due items, items due today, items due tomorrow and items
        due in 7 days.
    """
    (
        past_due_reminders,
        day_of_reminders,
        day_before_reminders,
        week_before_reminders,
    ) = [], [], [], []
    if reminders:
        for r in reminders:
            due_date = datetime.strptime(r[5], "%Y-%m-%d").date()
            today = datetime.today().date()
            if due_date < today:
                past_due_reminders.append(r)
            if due_date == today:
                day_of_reminders.append(r)
            if due_date == (datetime.today() + timedelta(days=1)).date():
                day_before_reminders.append(r)
            if due_date == (datetime.today() + timedelta(days=7)).date():
                week_before_reminders.append(r)
    return (
        past_due_reminders,
        day_of_reminders,
        day_before_reminders,
        week_before_reminders,
    )


def create_message_string(
    user_data: Optional[sqlite3.Cursor],
    reminders_by_category: Tuple[list[str], list[str], list[str], list[str]],
) -> str:
    """
    Creates a string of reminders notifications for the notifications popup.

    Args:
        user_data (Optional[sqlite3.Cursor]): Cursor object containg user
        preferences.
        reminders_by_category
        (Tuple[list[str], list[str], list[str], list[str]]): A tuple containing
        the categorized reminders for notification.

    Returns:
        str: A string representation of a bulleted list of reminders for
        display in the notifications popup.
    """
    # Create a string to hold reminders for notification.
    messages = ""
    # Create the list of notification messages starting with past due.
    for r in reminders_by_category[0]:
        messages += f"\u2022 Past due: {r[1]}\n"
    # Get 'day of' notificatons, if opted for.
    if user_data[3]:
        for r in reminders_by_category[1]:
            messages += f"\u2022 Due today: {r[1]}\n"
    # Get 'day before' notificatons, if opted for.
    if user_data[2]:
        for r in reminders_by_category[2]:
            messages += f"\u2022 Due tomorrow: {r[1]}\n"
    # Get 'week before' notificatons, if opted for.
    if user_data[1]:
        for r in reminders_by_category[3]:
            messages += f"\u2022 Due in 7 days: {r[1]}\n"
    return messages
