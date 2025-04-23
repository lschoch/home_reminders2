import os
import sqlite3
import sys
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk

from dateutil.relativedelta import relativedelta
from memory_profiler import profile
from tkcalendar import Calendar

from classes import InfoMsgBox, NofificationsPopup


# create treeview to display data from database
def create_tree_widget(self):
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

    return tree


# function to destroy existing toplevels to prevent them from accumulating.
def remove_toplevels(self):
    for widget in self.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.destroy()


# function to insert data from database into the treeview,
# use id as tag to color rows, item[5] is date_next
@profile
def insert_data(self, data):
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


# function to select date from a calendar
@profile
def get_date(date_last_entry, top):
    # destroy calendar if it already exists
    # (prevents multiple overlying calendars on repeatedly clicking the entry)
    for child in top.winfo_children():
        if isinstance(child, tk.Toplevel):
            child.destroy()

    # update date_last_entry after date is selected with OK button
    def cal_done():
        date_last_entry.delete(0, tk.END)
        date_last_entry.insert(0, cal.selection_get())
        top2.wm_overrideredirect(False)
        top2.destroy()

    def cal_cancel():
        top2.wm_overrideredirect(False)
        top2.destroy()

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
    ttk.Button(top2, text="ok", width=3, command=cal_done).grid(
        row=1, column=0, padx=(80, 0), pady=3, sticky="w"
    )
    ttk.Button(top2, text="cancel", width=6, command=cal_cancel).grid(
        row=1, column=0, padx=(0, 80), sticky="e"
    )
    # bind CalendarSelected event to function that sets date_last_entry
    cal.bind("<<CalendarSelected>>", on_cal_selection_changed)


# function to update treeview and labels after a change to the database
@profile
def refresh(self):
    # connect to database and create cursor
    with get_con() as self.con:
        self.cur = self.con.cursor()
        # select data depending on the current view
        if self.view_current:
            refreshed_data = self.cur.execute("""
                SELECT * FROM reminders
                WHERE date_next >= DATE('now', 'localtime')
                                     OR date_next IS NULL
                ORDER BY date_next ASC, description ASC
            """)
        else:
            refreshed_data = self.cur.execute("""
                SELECT * FROM reminders
                ORDER BY date_next ASC, description ASC
            """)

        for item in self.tree.get_children():
            self.tree.delete(item)

        insert_data(self, refreshed_data)
        self.refreshed = True

        if self.view_current:
            view_msg = (
                "Viewing pending items only. Select item to update or delete "
            )
        else:
            view_msg = "Viewing all items.  Select item to update or delete"

        # get nummber of past due items
        number_past_due_items = len(
            self.cur.execute("""
                SELECT * FROM reminders
                WHERE date_next < DATE('now', 'localtime')
                                     OR date_next IS NULL
            """).fetchall()
        )

        if number_past_due_items == 1:
            expired_msg = f"{number_past_due_items} past due item"
        else:
            expired_msg = f"{number_past_due_items} past due items"
        self.view_lbl_msg.set(view_msg)
        self.view_lbl.config(background="#ececec")
        self.expired_lbl_msg.set(expired_msg)


# function to calculate date_next
@profile
def date_next_calc(date_last, frequency, period):
    match period:
        case "":
            date_next = ""
        case "one-time":
            date_next = datetime.strptime(date_last, "%Y-%m-%d").date()
            date_next = date_next.strftime("%Y-%m-%d")
        case "days":
            date_next = datetime.strptime(
                date_last, "%Y-%m-%d"
            ).date() + timedelta(days=frequency)
            date_next = date_next.strftime("%Y-%m-%d")
        case "weeks":
            date_next = datetime.strptime(
                date_last, "%Y-%m-%d"
            ).date() + timedelta(weeks=frequency)
            date_next = date_next.strftime("%Y-%m-%d")
        case "months":
            date_next = datetime.strptime(
                date_last, "%Y-%m-%d"
            ).date() + relativedelta(months=frequency)
            date_next = date_next.strftime("%Y-%m-%d")
        case "years":
            date_next = datetime.strptime(
                date_last, "%Y-%m-%d"
            ).date() + relativedelta(years=frequency)
            date_next = date_next.strftime("%Y-%m-%d")
    return date_next


# create a validation function
@profile
def valid_frequency(input_data):
    if input_data:
        try:
            float(input_data)
            return True
        except ValueError:
            return False
    else:
        return False


# function to create database connection
@profile
def get_con():
    dir_path = os.path.join(appsupportdir(), "Home Reminders")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    file_path = os.path.join(dir_path, "home_reminders.db")
    return sqlite3.connect(file_path)


@profile
def appsupportdir():
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


@profile
def pathinappsupportdir(*paths, create=False):
    location = os.path.join(appsupportdir(), *paths)

    if create:
        os.makedirs(location)

    return location


# initialize user data if the table is empty
@profile
def initialize_user():
    with get_con() as con:
        cur = con.cursor()
        empty_check = cur.execute("SELECT COUNT(*) FROM user").fetchall()
        if empty_check[0][0] == 0:
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


# get/modify user preferences and store in user table
@profile
def get_user_data(self):  # noqa: PLR0915
    def submit():
        with get_con() as con:
            cur = con.cursor()
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
                num_window.focus_set()
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
                num_window.focus_set()
            else:
                values = (
                    num,  # phone number
                    var1.get(),  # week before
                    var2.get(),  # day before
                    var3.get(),  # day of
                    # last notification date:
                    datetime.strftime(date.today(), "%Y-%m-%d"),
                )
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
                num_window.destroy()
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

    # get existing user preferences, if present
    with get_con() as con:
        cur = con.cursor()
        # initialize user table if it's empty
        initialize_user()
        user_data = cur.execute("SELECT * FROM user").fetchone()
    if user_data[0] is not None:
        user_exists = True
    else:
        user_exists = False

    # create window for user to input/modify preferences
    num_window = tk.Toplevel(self)
    num_window.title("Notifications")
    num_window.configure(background="#ececec")  # "#ffc49c")
    num_window.geometry("300x185+100+50")
    num_window.resizable(False, False)
    num_window.wm_transient(self)
    num_window.wait_visibility()
    num_window.grab_set()
    num_window.grid_columnconfigure(0, weight=1)
    num_window.grid_columnconfigure(1, weight=1)

    # create widgets for the window
    ttk.Label(
        num_window,
        text="Enter your ten digit phone number:",
        anchor="center",
        background="#ececec",  # "#ececec",
        font=("Helvetica", 13),
    ).grid(row=0, column=0, columnspan=2, pady=(15, 7))
    entry = ttk.Entry(num_window, font=("Helvetica", 13), width=10)
    entry.grid(row=1, column=0, columnspan=2)

    var1 = tk.IntVar()
    var2 = tk.IntVar()
    var3 = tk.IntVar()

    ttk.Label(
        num_window,
        text="Notify when? Select all that apply:",
        anchor="center",
        background="#ececec",  # "#ececec",
        font=("Helvetica", 13),
    ).grid(row=2, column=0, columnspan=2, pady=(18, 2))

    c1 = tk.Checkbutton(
        num_window,
        text="Week before",
        font=("Helvetica", 12),
        variable=var1,
        onvalue=1,
        offvalue=0,
        background="#ececec",  # "#ececec",
    )
    c1.grid(row=3, column=0, columnspan=2, padx=(20, 0), sticky="w")
    c2 = tk.Checkbutton(
        num_window,
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
        num_window,
        text="Day of",
        font=("Helvetica", 12),
        variable=var3,
        onvalue=1,
        offvalue=0,
        background="#ececec",  # "#ececec",
    )
    c3.grid(row=3, column=0, columnspan=2, padx=(0, 25), sticky="e")

    ttk.Button(num_window, text="Submit", width=6, command=submit).grid(
        row=4, column=0, padx=(0, 15), pady=15, sticky="e"
    )
    ttk.Button(
        num_window, text="Cancel", width=6, command=num_window.destroy
    ).grid(row=4, column=1, padx=(15, 0), pady=15, sticky="w")

    # insert pre-existing phone number and notification frequencies, if present
    if user_data[0] is not None:
        entry.insert(0, user_data[0])
        var1.initialize(user_data[1])
        var2.initialize(user_data[2])
        var3.initialize(user_data[3])

    entry.focus_set()


# notifications popup for upcoming items
@profile
def notifications_popup(self):
    # remove existing notifications popups, if any exist
    for widget in self.winfo_children():
        if (
            isinstance(widget, tk.Toplevel)
            and widget.title() == "Notifications"
        ):
            widget.destroy()

    # initialize user table if it's empty
    initialize_user()
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


# end notifications popup for upcoming events


# function to create database and table if they do not exist and retrieve data
def get_data(db_path):
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


###############################################################
# function to display current date and update treeview when date changes
@profile
def refresh_date(self, data):
    # catch the date change at midnight
    if self.todays_date_var.get() < datetime.now().strftime("%Y-%m-%d"):
        self.todays_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        """ # refresh all data
        refresh(self)
        insert_data(self, data) """
    # create widget
    self.today_is_lbl = tk.Label(
        self,
        # textvariable=self.todays_date_var,
        text=f"Today is {self.todays_date_var.get()}",
        foreground="black",
        font=("Helvetica", 24),
    )
    self.today_is_lbl.grid(row=0, column=1, pady=(10, 0), sticky="n")


# end function to display current date
###############################################################


def quit_program():
    sys.exit()
