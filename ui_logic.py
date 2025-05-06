import sqlite3
import tkinter as tk
from datetime import date, datetime
from tkinter import END, Menu, ttk
from typing import Any

from icecream import ic  # noqa: F401

from business_logic import (
    backup,
    date_next_calc,
    delete_all,
    delete_item_from_database,
    get_con,
    get_date,
    get_user_data,
    on_treeview_selection_changed,
    opt_in,
    opt_out,
    preferences,
    refresh,
    restore,
    save_prefs,
    validate_inputs,
    view_all,
    view_pending,
)
from classes import InfoMsgBox, TopLvl, YesNoMsgBox


def create_menu_bar(self):
    self.option_add("*tearOff", False)
    menubar = Menu(self)
    self.config(menu=menubar)

    notifications_menu = Menu(menubar)
    menubar.add_cascade(label="Notifications", menu=notifications_menu)
    notifications_menu.add_command(
        label="Opt-in", command=lambda: opt_in(self)
    )
    notifications_menu.add_command(
        label="Opt-out", command=lambda: opt_out(self)
    )
    notifications_menu.add_command(
        label="Preferences", command=lambda: preferences(self)
    )

    view_menu = Menu(menubar)
    menubar.add_cascade(label="View", menu=view_menu)
    view_menu.add_command(label="Pending", command=lambda: view_pending(self))
    view_menu.add_command(label="All", command=lambda: view_all(self))

    data_menu = Menu(menubar)
    menubar.add_cascade(label="Data", menu=data_menu)
    data_menu.add_command(label="Backup", command=lambda: backup(self))
    data_menu.add_command(label="Restore", command=lambda: restore(self))
    data_menu.add_command(label="Delete All", command=lambda: delete_all(self))


def create_legend(self):
    """create legend for colors in treeview"""
    self.legend_frame = tk.Frame(self)
    self.legend_frame.grid(row=1, column=0, pady=(0, 20), sticky="s")

    tk.Label(
        self.legend_frame,
        text="Legend:",
        justify="center",
        font=("Arial", 14),
        foreground="black",
        background="#ececec",
    ).grid(row=0, column=0, pady=(5, 0), columnspan=2)

    tk.Label(
        self.legend_frame,
        text="  ",
        width=2,
        background="lime",
        borderwidth=1,
        relief="solid",
    ).grid(
        row=1,
        column=1,
        pady=(5, 0),
    )
    ttk.Label(
        self.legend_frame, text="due today - ", background="#ececec"
    ).grid(row=1, column=0, padx=(5, 0), pady=(5, 0), sticky="e")

    tk.Label(
        self.legend_frame,
        text="  ",
        width=2,
        background="yellow",
        borderwidth=1,
        relief="solid",
    ).grid(
        row=2,
        column=1,
        pady=(5, 0),
    )
    ttk.Label(
        self.legend_frame, text="past due - ", background="#ececec"
    ).grid(row=2, column=0, padx=(5, 0), pady=(5, 0), sticky="e")

    tk.Label(
        self.legend_frame,
        text="  ",
        width=2,
        background="white",
        borderwidth=1,
        relief="solid",
    ).grid(
        row=3,
        column=1,
        pady=(5, 0),
    )
    ttk.Label(self.legend_frame, text="pending - ", background="#ececec").grid(
        row=3, column=0, padx=(5, 0), pady=(5, 0), sticky="e"
    )


def create_left_side_buttons(self):
    """create left side buttons for the main window"""
    self.btn_new = ttk.Button(
        self, text="New Item", command=lambda: create_new(self)
    )
    self.btn_new.grid(row=1, column=0, padx=20, pady=(20, 0), sticky="n")
    self.btn_quit = ttk.Button(self, text="Quit", command=self.destroy)
    self.btn_quit.grid(row=1, column=0, padx=20, pady=(60, 0), sticky="n")


def create_preferences_window(self):
    """
    Create window for users to input/modify their notification preferences.
    """

    def submit():
        week_before = self.var1.get()
        day_before = self.var2.get()
        day_of = self.var3.get()
        none_selected = not any([week_before, day_before, day_of])
        num = entry.get()
        # validate the entered phone number
        if not num.isnumeric() or len(num) > 10 or len(num) < 10:
            InfoMsgBox(
                self,
                "Notifications",
                "Phone number must be a ten digit numeric.",
                x_offset=100,
                y_offset=15,
            )
            entry.focus_set()
            return
        # require at least one "when" option
        elif none_selected:
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
            return
        else:
            values = (
                num,  # phone number
                week_before,  # week before
                day_before,  # day before
                day_of,  # day of
                # last notification date:
                datetime.strftime(date.today(), "%Y-%m-%d"),
            )
            save_prefs(self, values)
            preferences_window.destroy()

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

    self.var1 = tk.IntVar()
    self.var2 = tk.IntVar()
    self.var3 = tk.IntVar()

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
        variable=self.var1,
        onvalue=1,
        offvalue=0,
        background="#ececec",
    )
    c1.grid(row=3, column=0, columnspan=2, padx=(20, 0), sticky="w")
    c2 = tk.Checkbutton(
        preferences_window,
        text="Day before",
        font=("Helvetica", 12),
        variable=self.var2,
        onvalue=1,
        offvalue=0,
        background="#ececec",  # "#ececec",
    )
    c2.grid(row=3, column=0, columnspan=2, padx=(25, 0))

    c3 = tk.Checkbutton(
        preferences_window,
        text="Day of",
        font=("Helvetica", 12),
        variable=self.var3,
        onvalue=1,
        offvalue=0,
        background="#ececec",  # "#ececec",
    )
    c3.grid(row=3, column=0, columnspan=2, padx=(0, 25), sticky="e")

    ttk.Button(
        preferences_window,
        text="Submit",
        width=6,
        command=submit,
    ).grid(row=4, column=0, padx=(0, 15), pady=15, sticky="e")
    ttk.Button(
        preferences_window,
        text="Cancel",
        width=6,
        command=preferences_window.destroy,
    ).grid(row=4, column=1, padx=(15, 0), pady=15, sticky="w")

    # Get existing preferences, if present, and insert into preferences window.
    user_data = get_user_data(self)
    if user_data[
        0
    ]:  # user_data[0] = phone number. Indicates that user exists.
        entry.insert(0, user_data[0])
        self.var1.set(user_data[1])  # week_before
        self.var2.set(user_data[2])  # day_before
        self.var3.set(user_data[3])  # day_of

    entry.focus_set()


def create_edit_window(self, selected_item):
    remove_toplevels(self)
    # create toplevel
    top = TopLvl(self, "Edit Selection")

    # populate entries with data from the selection
    top.description_entry.insert(0, self.tree.item(selected_item)["values"][1])
    top.frequency_entry.insert(0, self.tree.item(selected_item)["values"][2])

    # use index function to determine index of the period_combobox value
    indx = top.period_list.index(self.tree.item(selected_item)["values"][3])
    # set the combobox value using current function
    top.period_combobox.current(indx)
    top.date_last_entry.insert(0, self.tree.item(selected_item)["values"][4])
    top.note_entry.insert(0, self.tree.item(selected_item)["values"][6])

    # bind click in date_last_entry to get_date
    top.date_last_entry.bind(
        "<1>", lambda e: get_date(top.date_last_entry, top)
    )

    # update database
    def update_item() -> Any:
        """
        Function to save the new data to the database after a reminder item has
        been edited. Does not return anything.
        """
        id = self.tree.item(selected_item)["values"][0]
        # validate inputs before saving, exit if validation fails
        validate = validate_inputs(self, top, id)
        if not validate:
            return
        # calculate date_next
        date_next = date_next_calc(top)
        # set frequency to 1 if period is "one-time"
        if top.period_combobox.get() == "one-time":
            top.frequency_entry.delete(0, END)
            top.frequency_entry.insert(0, "1")
        try:
            with get_con() as con:
                cur = con.cursor()
                cur.execute(
                    """
                    UPDATE reminders
                    SET (
                    description, frequency, period, date_last, date_next, \
                        note)
                    = (?, ?, ?, ?, ?, ?)
                    WHERE id = ? """,
                    (
                        top.description_entry.get(),
                        top.frequency_entry.get(),
                        top.period_combobox.get(),
                        top.date_last_entry.get(),
                        date_next,
                        top.note_entry.get(),
                        self.tree.item(selected_item)["values"][0],
                    ),
                )
                con.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            InfoMsgBox(self, "Error", "Failed to update the database.")
        refresh(self)
        remove_toplevels(self)

    def delete_item() -> Any:
        """
        Function to delete the selected reminder item from the database. Does
        not return anything.
        """
        answer = YesNoMsgBox(
            self,
            "Delete Reminder",
            "Are you sure you want to delete  \
                this reminder?",
        )
        if not answer.get_response():
            return
        id = self.tree.item(selected_item)["values"][0]
        delete_item_from_database(self, id)
        refresh(self)
        remove_toplevels(self)

    ttk.Button(top, text="Update", command=update_item).grid(
        row=2, column=1, pady=(15, 0), sticky="w"
    )

    ttk.Button(top, text="Delete", command=delete_item).grid(
        row=2, column=3, pady=(15, 0), sticky="w"
    )

    ttk.Button(
        top, text="Cancel", command=lambda: remove_toplevels(self)
    ).grid(row=2, column=5, pady=(15, 0), sticky="w")


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
        validate = validate_inputs(self, top)
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

    tree.bind(
        "<<TreeviewSelect>>",
        lambda event: on_treeview_selection_changed(self, event),
    )
    tree.grid(row=1, column=1)

    # add a scrollbar
    scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=1, column=2, pady=(0, 0), sticky="ns")
    return tree


def remove_toplevels(self) -> Any:
    """
    Function to destroy existing toplevels to prevent them from accumulating.
    """
    for widget in self.winfo_children():
        if isinstance(widget, tk.Toplevel):
            widget.destroy()
