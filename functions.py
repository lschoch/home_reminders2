import os
import sqlite3
import sys
import tkinter as tk
from datetime import date, datetime, timedelta  # noqa: F401
from tkinter import ttk

from dateutil.relativedelta import relativedelta
from tkcalendar import Calendar


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
                self.tree.tag_configure(item[0], background="lightblue")
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
    top2.wm_overrideredirect(True)

    top2.configure(background="#cacaca")
    x = top.winfo_x()
    y = top.winfo_y()
    # top2.geometry("+%d+%d" % (x + 48, y + 195))  # y + 120
    top2.geometry("+%d+%d" % (x + 18, y + 110))

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


# function to update treeview after change to database
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
    # connect to database and create cursor
    if getattr(sys, "frozen", False):
        # Running in a PyInstaller bundle
        base_dir = sys._MEIPASS
    else:
        # Running as a normal script
        base_dir = os.path.dirname(os.path.abspath(__file__))

    db_path = os.path.join(base_dir, "home_reminders.db")
    return sqlite3.connect(db_path)
