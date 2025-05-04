from __future__ import annotations

import os
import shutil
import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import END, ttk
from typing import Any, Optional, Tuple  # noqa: F401

from dateutil.relativedelta import relativedelta  # type: ignore
from tkcalendar import Calendar  # type: ignore

from classes import (
    InfoMsgBox,
    NofificationsPopup,
    TopLvl,
    YesNoMsgBox,
)


def create_tree_widget(self):
    """
    Function to create treeview to display the list of reminder items retrieved
    from the database. Returns tkinter.ttk,.Treeview object.
    """
    columns = (
        "id",
        "description",
        "frequency",
        "period",
        "date_last",
        "date_next",
        "note",
    )
    tree = ttk.Treeview(self, columns=columns, show="headings")

    # define headings and columns
    tree.heading("id", text="Id")
    tree.heading("description", text="Item", anchor="w")
    tree.heading("frequency", text="Frequency")
    tree.heading("period", text="Period", anchor="w")
    tree.heading("date_last", text="Last")
    tree.heading("date_next", text="Next")
    tree.heading("note", text="Note", anchor="w")
    tree.column("id", width=50, anchor="center")
    tree.column("description", width=250, anchor="w")
    tree.column("frequency", width=65, anchor="center")
    tree.column("period", width=75, anchor="w")
    tree.column("date_last", width=100, anchor="center")
    tree.column("date_next", width=100, anchor="center")
    tree.column("note", width=350, anchor="w")
    displaycolumns = (
        "description",
        "frequency",
        "period",
        "date_last",
        "date_next",
        "note",
    )
    tree["displaycolumns"] = displaycolumns

    tree.bind("<<TreeviewSelect>>", self.on_treeview_selection_changed)
    tree.grid(row=1, column=1)

    # add a scrollbar
    scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=1, column=2, pady=(0, 0), sticky="ns")
    print(f"+++++++++++++++++++++++++++++ {type(tree)}")
    return tree


def remove_toplevels(self) -> Any:
    """
    Function to destroy existing toplevels to prevent them from accumulating.
    """
    for widget in self.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.destroy()


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
    # connect to database and create cursor
    try:
        with get_con() as con:
            cur = con.cursor()
            # select data depending on the current view
            if self.view_current:
                refreshed_data = cur.execute("""
                    SELECT * FROM reminders
                    WHERE date_next >= DATE('now', 'localtime')
                                        OR date_next IS NULL
                    ORDER BY date_next ASC, description ASC
                """)
            else:
                refreshed_data = cur.execute("""
                    SELECT * FROM reminders
                    ORDER BY date_next ASC, description ASC
                """)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")

    for item in self.tree.get_children():
        self.tree.delete(item)

    insert_data(self, refreshed_data)
    self.refreshed = True

    if self.view_current:
        view_msg = (
            "Viewing pending items only - select an item to edit or delete."
        )
    else:
        view_msg = "Viewing all items - select an item to edit or delete."

    # get nummber of past due items
    try:
        with get_con() as con:
            self.cur = con.cursor()
            number_past_due_items = len(
                self.cur.execute("""
                    SELECT * FROM reminders
                    WHERE date_next < DATE('now', 'localtime')
                                        OR date_next IS NULL
                """).fetchall()
            )
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    if number_past_due_items == 1:
        expired_msg = f"{number_past_due_items} past due item"
    else:
        expired_msg = f"{number_past_due_items} past due items"
    self.view_lbl_msg.set(view_msg)
    self.view_lbl.config(background="#ececec")
    self.expired_lbl_msg.set(expired_msg)


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
    Function to initialize the user table if it is empty. Does not return
    anything.
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


def get_user_data(self) -> Any:  # noqa: PLR0915
    """
    Function to get user data for notifications preferences. It creates a
    window for the user to input their phone number and notification
    preferences. It validates the input and updates the database with the
    user's preferences. If the user already exists, it updates their data.
    It also checks if the user has already opted in to notifications and
    initializes the user table if it is empty. It does not return anything.
    """

    def submit() -> Any:
        """
        Function to save user preferences to the database. User enters
        preferences in popup window and clicks submit button to write this data
        to the user table of the database. Does not return anything.
        """
        num = entry.get()
        no_options_selected = (
            var1.get() == 0 and var2.get() == 0 and var3.get() == 0
        )
        # validate the entered phone number
        if not num.isnumeric() or len(num) > 10 or len(num) < 10:
            InfoMsgBox(
                self,
                "Notifications",
                "Phone number must be a ten digit numeric.",
                x_offset=100,
                y_offset=15,
            )
            preferences_window.focus_set()
            entry.focus_set()
        # require at least one "when" option
        elif no_options_selected:
            txt = (
                "Please select at least one option for when "
                + "to be notified."
            )
            InfoMsgBox(
                self,
                "Notifications",
                txt,
                x_offset=100,
                y_offset=15,
            )
            preferences_window.focus_set()
        else:
            values = (
                num,  # phone number
                var1.get(),  # week before
                var2.get(),  # day before
                var3.get(),  # day of
                # last notification date:
                datetime.strftime(date.today(), "%Y-%m-%d"),
            )
        try:
            with get_con() as con:
                cur = con.cursor()
                cur.execute("DELETE FROM user")
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
        preferences_window.destroy()
        if user_exists:
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

    # initialize user table if it's empty
    initialize_user(self)
    # get existing user preferences
    try:
        with get_con() as con:
            cur = con.cursor()
            # check if user table is empty
            cur.execute("SELECT COUNT(*) FROM user")
            user_data = cur.execute("SELECT * FROM user").fetchone()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    if user_data[0] is not None:
        user_exists = True
    else:
        user_exists = False

    # create window for user to input/modify preferences
    preferences_window = tk.Toplevel(self)
    preferences_window.title("Notifications")
    preferences_window.configure(background="#ececec")  # "#ffc49c")
    preferences_window.geometry("300x185+100+50")
    preferences_window.resizable(False, False)
    preferences_window.wm_transient(self)
    preferences_window.wait_visibility()
    preferences_window.grab_set()
    preferences_window.grid_columnconfigure(0, weight=1)
    preferences_window.grid_columnconfigure(1, weight=1)

    # create widgets for the window
    ttk.Label(
        preferences_window,
        text="Enter your ten digit phone number:",
        anchor="center",
        background="#ececec",
        font=("Helvetica", 13),
    ).grid(row=0, column=0, columnspan=2, pady=(15, 7))
    entry = ttk.Entry(preferences_window, font=("Helvetica", 13), width=10)
    entry.grid(row=1, column=0, columnspan=2)

    var1 = tk.IntVar()
    var2 = tk.IntVar()
    var3 = tk.IntVar()

    ttk.Label(
        preferences_window,
        text="Notify when? Select all that apply:",
        anchor="center",
        background="#ececec",
        font=("Helvetica", 13),
    ).grid(row=2, column=0, columnspan=2, pady=(18, 2))

    c1 = tk.Checkbutton(
        preferences_window,
        text="Week before",
        font=("Helvetica", 12),
        variable=var1,
        onvalue=1,
        offvalue=0,
        background="#ececec",
    )
    c1.grid(row=3, column=0, columnspan=2, padx=(20, 0), sticky="w")
    c2 = tk.Checkbutton(
        preferences_window,
        text="Day before",
        font=("Helvetica", 12),
        variable=var2,
        onvalue=1,
        offvalue=0,
        background="#ececec",  # "#ececec",
    )
    c2.grid(
        row=3,
        column=0,
        columnspan=2,
        padx=(25, 0),
    )

    c3 = tk.Checkbutton(
        preferences_window,
        text="Day of",
        font=("Helvetica", 12),
        variable=var3,
        onvalue=1,
        offvalue=0,
        background="#ececec",  # "#ececec",
    )
    c3.grid(row=3, column=0, columnspan=2, padx=(0, 25), sticky="e")

    ttk.Button(
        preferences_window, text="Submit", width=6, command=submit
    ).grid(row=4, column=0, padx=(0, 15), pady=15, sticky="e")
    ttk.Button(
        preferences_window,
        text="Cancel",
        width=6,
        command=preferences_window.destroy,
    ).grid(row=4, column=1, padx=(15, 0), pady=15, sticky="w")

    # insert pre-existing phone number and notification frequencies, if present
    if user_data[0] is not None:
        entry.insert(0, user_data[0])
        var1.initialize(user_data[1])
        var2.initialize(user_data[2])
        var3.initialize(user_data[3])

    entry.focus_set()


def notifications_popup(self) -> Any:  # noqa: C901, PLR0912, PLR0915
    """
    Function to check for upcoming items and create a notifications popup if
    there are any. It checks for items that are past due, due today, due
    tomorrow, or due in 7 days, depending on user preferences. It runs every
    4 hours to check for upcoming items. It also removes any existing
    notifications popups to prevent multiple popups from accumulating. Does not
    return anything.
    """
    # remove existing notifications popups, if any exist
    for widget in self.winfo_children():
        if (
            isinstance(widget, tk.Toplevel)
            and widget.title() == "Notifications"
        ):
            widget.destroy()

    # initialize user table if it's empty
    initialize_user(self)
    # check whether user has opted in to notifications
    try:
        with get_con() as con:
            cur = con.cursor()
            user_data = cur.execute("SELECT * FROM user").fetchone()
            # check whether user has entered a phone number (opted in)
            if user_data[0] is not None:
                # create a string to hold upcoming items
                messages = ""
                date = datetime.today().strftime("%Y-%m-%d")
                # check whether user wants 'day of' notificatons
                past_due_items = cur.execute(
                    """
                    SELECT * FROM reminders WHERE date_next < ?
                    ORDER BY date_next ASC""",
                    (date,),
                ).fetchall()
                for item in past_due_items:
                    messages += f"\u2022 Past due: {item[1]}\n"
                if user_data[3]:
                    date = datetime.today().strftime("%Y-%m-%d")
                    day_of_items = cur.execute(
                        """
                        SELECT * FROM reminders WHERE date_next == ?
                        ORDER BY date_next ASC""",
                        (date,),
                    ).fetchall()
                    for item in day_of_items:
                        messages += f"\u2022 Due today: {item[1]}\n"
                # check whether user wants 'day before' notificatons
                if user_data[2]:
                    date = (datetime.today() + timedelta(days=1)).strftime(
                        "%Y-%m-%d"
                    )
                    day_before_items = cur.execute(
                        """
                        SELECT * FROM reminders WHERE date_next == ?
                        ORDER BY date_next ASC""",
                        (date,),
                    ).fetchall()
                    for item in day_before_items:
                        messages += f"\u2022 Due tomorrow: {item[1]}\n"
                # check whether user wants 'week before' notificatons
                if user_data[1]:
                    date = (datetime.today() + timedelta(days=7)).strftime(
                        "%Y-%m-%d"
                    )
                    week_before_items = cur.execute(
                        """
                        SELECT * FROM reminders WHERE date_next == ?
                        ORDER BY date_next ASC""",
                        (date,),
                    ).fetchall()
                    for item in week_before_items:
                        messages += f"\u2022 Due in 7 days: {item[1]}\n"
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    # if there are any messages, create a notifications popup
    if messages:
        # remove the trailing \n from messages
        messages = messages[:-1]
        notifications_win = NofificationsPopup(
            self,
            title="Notifications",
            message="",
            x_offset=310,
            y_offset=400,
        )
        # add color to messages
        message_list = messages.split("\n")
        line_num = 1
        for msg in message_list:
            if msg.startswith("\u2022 Past due"):
                notifications_win.txt.insert("end", msg + "\n")
                indx_start = str(line_num) + ".0"
                indx_end = str(line_num + 1) + ".0"
                notifications_win.txt.tag_add("yellow", indx_start, indx_end)
                notifications_win.txt.tag_config("yellow", background="yellow")
                line_num += 1
            elif msg.startswith("\u2022 Due today"):
                notifications_win.txt.insert("end", msg + "\n")
                indx_start = str(line_num) + ".0"
                indx_end = str(line_num + 1) + ".0"
                notifications_win.txt.tag_add("lime", indx_start, indx_end)
                notifications_win.txt.tag_config("lime", background="lime")
                line_num += 1
            else:
                notifications_win.txt.insert("end", msg + "\n")
                line_num += 1

    # check every 4 hours whether a notifications popup is indicated.
    self.after(14400000, notifications_popup, self)


def date_check(self) -> Any:
    """
    Takes self as a parameter and checks if the current date has changed.
    If it has, updates the today_is_lbl to the current date and refreshes
    treeview so that highlighting remains accurate. This is done because the
    app is meant to remain open for extended periods. This function calls
    itself every second to monitor for date change. Does not return anything.
    """
    # check if the current date has changed
    if self.todays_date_var.get() != datetime.now().strftime("%Y-%m-%d"):
        # update the label to show today's date
        self.todays_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        self.today_is_lbl.config(
            text=f"Today is {self.todays_date_var.get()}",
        )
        # refresh data in treeview so that highlighting remains accurate
        refresh(self)

    self.after(1000, date_check, self)


def get_data(db_path: str | os.PathLike) -> Optional[sqlite3.Cursor]:
    """
    Function to create database if it does not exist and retrieve data for
    display in treeview. Takes the database path as parameter and returns a
    cursor object with data retrieved from the reminders table.
    """
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()

        # create user table to store user phone number and notification
        # preferences
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user(
                phone_number TEXT,
                week_before INT,
                day_before INT,
                day_of INT,
                last_notification_date TEXT)
        """)

        # create reminders table if it doesn't exist
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
        # retrieve data for display in treeview
        data = cur.execute("""
            SELECT * FROM reminders
            ORDER BY date_next ASC, description ASC
        """)
    return data


def validate_inputs(
    self, top, new: bool = False, id: int | None = None
) -> bool:
    """
    Function to validate inputs for a new item and update item dialogs.
    Returns True if inputs are valid, False otherwise.
    """
    # description is required
    if not top.description_entry.get():
        InfoMsgBox(
            self,
            "Invalid Input",
            "Description cannot be blank.",
        )
        top.description_entry.focus_set()
        return False
    # check for duplicate descriptions
    description = top.description_entry.get()
    try:
        with get_con() as con:
            cur = con.cursor()
            result = cur.execute("""SELECT * FROM reminders""")
            items = result.fetchall()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    # get original description if updating an existing item
    if id:
        for item in items:
            if item[0] == id:
                original_description = item[1]
    else:
        original_description = None
    for item in items:
        # item[1] is the item description in the database
        if item[1] == description:
            # alert if description already exists unless it's the
            # same item (ie, updating an existing item)

            # item[0] is the id in the database
            if new or (not new and item[0] != id):
                InfoMsgBox(
                    self,
                    "Duplicate Description",
                    "There is already an entry with this description."
                    + " Try again.",
                )
                # if updating an existing item, reset original
                # description
                if not new:
                    top.description_entry.delete(0, tk.END)
                    top.description_entry.insert(0, original_description)
                top.description_entry.focus_set()
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


# function to delete user data from the user table
def delete_user_data(self) -> Any:
    """
    Function to delete user data from the user table.
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
    """function to opt in to notifications and get user data"""
    # initialize user table if empty
    initialize_user(self)
    try:
        with get_con() as con:
            cur = con.cursor()
            # check to see if user has a phone number; i.e., already
            # receiving notifications
            phone_number = cur.execute("SELECT * FROM user").fetchone()[0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
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
            get_user_data(self)
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
    # if user opts out of notifications, delete user's data
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
                get_user_data(self)


def opt_out(self) -> Any:
    """
    Function giving user the choice to opt out of notifications. Does not
    return anything,
    """
    initialize_user(self)
    try:
        with get_con() as con:
            cur = con.cursor()
            # check to see if user has a phone number; i.e., already
            # receiving notifications
            phone_number = cur.execute("SELECT * FROM user").fetchone()[0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    if phone_number is not None:
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
    Function giving user the option to modify their notification preferences.
    Does not return anything.
    """
    initialize_user(self)
    # check to see if user has a phone number; i.e., already receiving
    # notifications
    try:
        with get_con() as con:
            cur = con.cursor()
            phone_number = cur.execute("SELECT * FROM user").fetchone()[0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    if phone_number:
        get_user_data(self)
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
    Changes the treeview to include only items due today or in the future.
    Does not return anything.
    """
    self.view_current = True
    try:
        with get_con() as con:
            cur = con.cursor()
            data = cur.execute("""
                SELECT * FROM reminders
                WHERE date_next >= DATE('now', 'localtime')
                ORDER BY date_next ASC, description ASC
            """)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    for item in self.tree.get_children():
        self.tree.delete(item)
    insert_data(self, data)
    refresh(self)
    remove_toplevels(self)
    self.refreshed = True
    self.tree.focus()


def view_all(self) -> Any:
    """
    Changes the treeview to include all items, including thise that are past
    due. Does not return anything.
    """
    self.view_current = False
    try:
        with get_con() as con:
            cur = con.cursor()
            data = cur.execute("""
                SELECT * FROM reminders
                ORDER BY date_next ASC, description ASC
            """)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        InfoMsgBox(self, "Error", "Failed to retrieve data from the database.")
    for item in self.tree.get_children():
        self.tree.delete(item)
    insert_data(self, data)
    refresh(self)
    remove_toplevels(self)
    self.refreshed = True
    self.focus_set()
    self.tree.focus_set()


def get_db_paths() -> tuple[str | os.PathLike, str | os.PathLike]:
    """
    Returns a two tuple: the first element is the path to the database and
    the second element is the path to the database backup.
    """
    db_base_path = os.path.join(appsupportdir(), "Home Reminders")
    if not os.path.exists(db_base_path):
        os.makedirs(db_base_path)
    db_path = os.path.join(db_base_path, "home_reminders.db")
    db_bak_path = os.path.join(db_base_path, "home_reminders.bak")
    return (db_path, db_bak_path)


def backup(self) -> Any:
    """
    Gives user the option to create a new database backup by copying the
    database file to a backup file. Does not return anything.
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
    Gives user the option to restore the database file by copying the backup
    file to the database file. Does not return anything.
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
    Gives user the option to delete the database file. Does not return
    anything.
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


def create_new(self) -> Any:
    """
    Function to create top level window for entry of new item. Does not return
    anything.
    """
    # remove any existing toplevels
    remove_toplevels(self)

    # create new toplevel
    top = TopLvl(self, "New Item")
    top.date_last_entry.insert(0, date.today())

    # bind click in date_last_entry to get_date
    top.date_last_entry.bind(
        "<1>", lambda e: get_date(top.date_last_entry, top)
    )

    # function to save new item to database
    def save_item():
        # validate inputs before saving, exit if validation fails
        validate = validate_inputs(self, top, new=True)
        if not validate:
            return

        # calculate date_next
        date_next = date_next_calc(top)
        # set frequency to 1 if period is "one-time"
        if top.period_combobox.get() == "one-time":
            top.frequency_entry.delete(0, END)
            top.frequency_entry.insert(0, "1")
        # get data to insert into database
        data_get = (
            top.description_entry.get(),
            top.frequency_entry.get(),
            top.period_combobox.get(),
            top.date_last_entry.get(),
            date_next,
            top.note_entry.get(),
        )
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
                    data_get,
                )
                con.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            InfoMsgBox(self, "Error", "Failed to update the database.")
        refresh(self)

        save_btn.config(state="normal")
        top.destroy()
        self.tree.focus()

    def cancel():
        # remove_toplevels(self)
        top.destroy()
        self.tree.focus()

    save_btn = ttk.Button(top, text="Save", command=save_item)
    save_btn.grid(row=2, column=1, padx=(33, 0), pady=(15, 0), sticky="w")

    ttk.Button(top, text="Cancel", command=cancel).grid(
        row=2, column=3, padx=(0, 48), pady=(15, 0), sticky="e"
    )
