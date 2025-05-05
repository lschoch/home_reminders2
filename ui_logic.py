import tkinter as tk
from datetime import date, datetime
from tkinter import Menu, ttk

from business_logic import (
    backup,
    create_new,
    delete_all,
    get_user_data,
    opt_in,
    opt_out,
    preferences,
    restore,
    save_prefs,
    view_all,
    view_pending,
)
from classes import InfoMsgBox


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
