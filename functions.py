import os
import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta
from tkinter import ttk

from dateutil.relativedelta import relativedelta
from tkcalendar import Calendar

from classes import InfoMsgBox

# from twilio.rest import Client


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
    tree.column("description", anchor="w")
    tree.column("frequency", width=65, anchor="center")
    tree.column("period", width=75, anchor="w")
    tree.column("date_last", width=100, anchor="center")
    tree.column("date_next", width=100, anchor="center")
    tree.column("note", width=200, anchor="w")

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
        self.tree.tag_configure(item[0], font=("Helvetica", 13))


# function to select date from a calendar
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
        # restore overrideredirect to False
        top2.wm_overrideredirect(False)
        top2.destroy()

    def cal_cancel():
        # restore overrideredirect to False
        top2.wm_overrideredirect(False)
        top2.destroy()

    # function to set date_last_entry from calendar click
    def on_cal_selection_changed(event):
        date_last_entry.delete(0, tk.END)
        date_last_entry.insert(0, cal.selection_get())
        # restore overrideredirect to False
        top2.wm_overrideredirect(False)
        top2.destroy()

    # create a toplevel for the calendar
    top2 = tk.Toplevel(top)

    # remove title bar
    # top2.wm_overrideredirect(True)

    top2.configure(background="#cacaca")
    x = top.winfo_x()
    y = top.winfo_y()
    # top2.geometry("+%d+%d" % (x + 48, y + 195))  # y + 120
    top2.geometry("+%d+%d" % (x + 187, y + 86))

    # keep calendar in front of it's parent window (only wm_transient works)
    # 1. top2.wm_transient(top)
    # 2. top2.wm_attributes("-topmost", True)
    # 3. top2.lift()
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


# function to update treeview after a change to the database
def refresh(self):
    # connect to database and create cursor
    self.con = get_con()
    self.cur = self.con.cursor()
    # select data depending on the current view (all vs future)
    if self.view_current:
        data = self.cur.execute("""
            SELECT * FROM reminders
            WHERE date_next >= DATE('now', 'localtime') OR date_next IS NULL
            ORDER BY date_next ASC, description ASC
        """)
    else:
        data = self.cur.execute("""
            SELECT * FROM reminders
            ORDER BY date_next ASC, description ASC
        """)

    for item in self.tree.get_children():
        self.tree.delete(item)

    insert_data(self, data)
    self.refreshed = True


# function to calculate date_next
def date_next_calc(date_last, frequency, period):
    match period:
        case "":
            date_next = ""
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
def valid_frequency(input_data):
    if input_data:
        try:
            float(input_data)
            return True
        except ValueError:
            return False
    else:
        return False


def check_expired(self):
    self.con = get_con()
    self.cur = self.con.cursor()
    result = self.cur.execute("""
        SELECT * FROM reminders
        WHERE date_next < DATE('now', 'localtime')
        ORDER BY date_next ASC
    """).fetchall()
    if result and self.view_current:
        msg = "Pending items - select a row to update or delete "
        self.lbl_msg.set(msg)
        self.lbl_color.set("#ececec")
        self.expired_msg.set('Click "All" to view past due items')
    elif self.view_current:
        self.lbl_msg.set("Pending items - select a row to update or delete")
        self.lbl_color.set("#ececec")
        self.expired_msg.set(f"{len(result)} past due")
    else:
        self.lbl_msg.set("All items - select a row to update or delete")
        self.lbl_color.set("#ececec")
        self.expired_msg.set(f"{len(result)} past due")
    self.view_lbl.config(background=self.lbl_color.get())


# function to create database connection
def get_con():
    dir_path = os.path.join(appsupportdir(), "Home Reminders")
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    file_path = os.path.join(dir_path, "home_reminders.db")
    return sqlite3.connect(file_path)


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


def pathinappsupportdir(*paths, create=False):
    location = os.path.join(appsupportdir(), *paths)

    if create:
        os.makedirs(location)

    return location


def send_sms():
    pass


# initialize user data if the table is empty
def initialize_user():
    con = get_con()
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


# get user data if user opts in for notifications
def get_user_data(self):
    def cancel():
        num_window.destroy()

    def submit():
        con = get_con()
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

    # get user data if it exists
    con = get_con()
    cur = con.cursor()
    # initialize user table if it's empty
    initialize_user()
    user_data = cur.execute("SELECT * FROM user").fetchone()
    if user_data[0] is not None:
        user_exists = True
    else:
        user_exists = False
    # create window for entry/modification of user data
    num_window = tk.Toplevel(self)
    num_window.title("Notifications")
    num_window.configure(background="#ececec") # "#ffc49c")
    num_window.geometry("300x185+100+50")
    num_window.resizable(False, False)
    num_window.wm_transient(self)
    num_window.wait_visibility()
    num_window.grab_set()
    num_window.grid_columnconfigure(0, weight=1)
    num_window.grid_columnconfigure(1, weight=1)
    ttk.Label(
        num_window,
        text="Enter your ten digit phone number:",
        anchor="center",
        background="#ececec",  # "#ececec",
        font=("Helvetica", 13),
    ).grid(row=0, column=0, columnspan=2, pady=(15, 7))
    entry = ttk.Entry(
        num_window,
        font=("Helvetica", 13),
        width=10)
    entry.grid(row=1, column=0, columnspan=2)
    # enter phone number if one exists
    if user_data[0] is not None:
        entry.insert(0, user_data[0])

    ttk.Label(
        num_window,
        text="Notify when? Select all that apply:",
        anchor="center",
        background="#ececec",  # "#ececec",
        font=("Helvetica", 13),
    ).grid(row=2, column=0, columnspan=2, pady=(18, 2))

    var1 = tk.IntVar()
    var2 = tk.IntVar()
    var3 = tk.IntVar()
    # if there is a phone number set the frequency options
    if user_data[0] is not None: 
        var1.initialize(user_data[1])
        var2.initialize(user_data[2])
        var3.initialize(user_data[3])
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
    ttk.Button(num_window, text="Cancel", width=6, command=cancel).grid(
        row=4, column=1, padx=(15, 0), pady=15, sticky="w"
    )
    entry.focus_set()
