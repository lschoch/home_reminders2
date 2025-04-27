import tkinter as tk
from tkinter import Menu, ttk

from business_logic import (
    backup,
    delete_all,
    opt_in,
    opt_out,
    preferences,
    restore,
    view_all,
    view_pending,
)


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
