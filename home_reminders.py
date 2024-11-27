import importlib
import os
import shutil
import sqlite3
import tkinter as tk
from datetime import date, datetime, timedelta  # noqa: F401
from tkinter import ttk

from PIL import Image, ImageTk
from tkmacosx import Button

from classes import InfoMsgBox, NofificationsPopup, TopLvl, YesNoMsgBox
from functions import (
    appsupportdir,
    check_expired,
    create_tree_widget,
    date_next_calc,
    get_con,
    get_date,
    get_user_data,
    initialize_user,
    insert_data,
    refresh,
    remove_toplevels,
    send_sms,  # noqa: F401
    valid_frequency,
)

# create splash screen
if "_PYI_SPLASH_IPC" in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash  # type: ignore

    pyi_splash.update_text("UI Loaded ...")
    pyi_splash.close()
    print("Splash screen closed.")

# connect to database and create cursor
dir_path = os.path.join(appsupportdir(), "Home Reminders")
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
db_path = os.path.join(dir_path, "home_reminders.db")
db_bak_path = os.path.join(dir_path, "home_reminders.bak")
con = sqlite3.connect(db_path)
cur = con.cursor()

# create table to store user phone number and notification preferences
cur.execute("""
    CREATE TABLE IF NOT EXISTS user(
        phone_number TEXT,
        week_before INT,
        day_before INT,
        day_of INT,
        last_notification_date TEXT)
""")

# create data table if it doesn't exist
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
    WHERE date_next >= DATE('now', 'localtime')
    ORDER BY date_next ASC, description ASC
""")


# create the main window
class App(tk.Tk):
    def __init__(self, **kw):  # noqa: PLR0915
        super().__init__(**kw)

        # get path to title bar icon
        base_dir = os.path.dirname(os.path.abspath(__file__))

        self.ico_path = os.path.join(base_dir, "images", "icons8-home-80.png")

        self.title("Home Reminders")
        ico = Image.open(self.ico_path)
        photo = ImageTk.PhotoImage(ico)
        self.wm_iconphoto(True, photo)
        self.geometry("1120x400+3+3")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.rowconfigure(0, minsize=120)

        # create variable to prevent calling
        # treeview_on_selection_changed after refresh
        self.refreshed = False

        # flag to track whether coming from view_all or view_current
        self.view_current = True

        self.lbl_msg = tk.StringVar()
        self.lbl_color = tk.StringVar()
        self.expired_msg = tk.StringVar()

        ####################################
        # add left side buttons
        self.btn = ttk.Button(self, text="Pending", command=self.pending).grid(
            row=1, column=0, padx=20, pady=(20, 0), sticky="n"
        )
        self.btn = ttk.Button(self, text="All", command=self.view_all).grid(
            row=1, column=0, padx=20, pady=(72, 0), sticky="n"
        )
        self.btn = ttk.Button(self, text="New", command=self.create_new).grid(
            row=1, column=0, padx=20, pady=(0, 72), sticky="s"
        )
        self.btn = ttk.Button(
            self, text="Quit", command=self.quit_program
        ).grid(row=1, column=0, padx=20, pady=(0, 20), sticky="s")
        # end left side buttons
        ####################################

        self.view_lbl = ttk.Label(
            self,
            textvariable=self.lbl_msg,
            background=self.lbl_color.get(),
            font=("Arial", 18),
        )
        self.view_lbl.grid(row=0, column=1, pady=(0, 35), sticky="s")

        self.expired_lbl = tk.Label(
            self,
            textvariable=self.expired_msg,
            background="yellow",
            borderwidth=1,
            relief="solid",
        )
        self.expired_lbl.grid(
            row=0, column=1, ipadx=4, ipady=4, pady=(0, 5), sticky="s"
        )

        # display current date
        date_variable = tk.StringVar()
        date_variable.set(f"Today is {date.today()}")

        self.today_is_lbl = tk.Label(
            self,
            textvariable=date_variable,
            foreground="black",
            font=("Helvetica", 24),
        )
        self.today_is_lbl.grid(row=0, column=1, pady=(10, 0), sticky="n")

        # insert image
        try:
            img_l = ImageTk.PhotoImage(Image.open(self.ico_path))
            self.img_lbl_l = tk.Label(self, image=img_l)
            self.img_lbl_l.image = img_l
            self.img_lbl_l.grid(row=0, column=0, sticky="ns")
        except FileNotFoundError:
            pass

        ####################################
        # create legend
        self.legend_frame = tk.Frame(
            # self, highlightbackground="black", highlightthickness=1
            self
        )
        self.legend_frame.grid(row=0, column=3, pady=(0, 40), sticky="s")

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
        ttk.Label(
            self.legend_frame, text="pending - ", background="#ececec"
        ).grid(row=3, column=0, padx=(5, 0), pady=(5, 0), sticky="e")
        # end legend
        ####################################

        ####################################
        # add right side buttons
        ttk.Button(self, text="Backup", command=self.backup).grid(
            row=1, column=3, padx=(20, 0), pady=(20, 0), sticky="n"
        )
        ttk.Button(self, text="Restore", command=self.restore).grid(
            row=1, column=3, padx=(20, 0), pady=(72, 0), sticky="n"
        )
        ttk.Button(self, text="Delete All", command=self.delete_all).grid(
            row=1, column=3, padx=(20, 0), pady=(0, 72), sticky="s"
        )
        Button(
            self,
            text="Notifications",
            bg="#ffc49c",  # background="#8BB7F0",
            height=35,
            width=120,
            focuscolor="black",  # "#ffc49c",
            focusthickness=1,
            command=self.notifications,
        ).grid(row=1, column=3, padx=(20, 0), pady=(0, 20), sticky="s")
        # end right side buttons
        ####################################

        # create treeview to display data
        self.tree = create_tree_widget(self)

        # add data to treeview
        insert_data(self, data)

        # set view_label message and color
        check_expired(self)

        #######################################
        # notifications for upcoming events
        #######################################
        # initialize user table if it's empty
        initialize_user()
        user_data = cur.execute("SELECT * FROM user").fetchone()
        # check whether user has entered a phone number; i.e., opted in for
        # notifications
        if user_data[0] is not None:
            # create a string to hold upcoming items
            messages = ""
            # check whether user wants 'day of' notificatons
            if user_data[3]:
                dat = datetime.today().strftime("%Y-%m-%d")
                day_of_items = cur.execute(
                    """
                    SELECT * FROM reminders WHERE date_next == ?""",
                    (dat,),
                ).fetchall()
                for item in day_of_items:
                    messages += f"\u2022 Due today: {item[1]}\n"
            # check whether user wants 'day before' notificatons
            if user_data[2]:
                dat = (datetime.today() + timedelta(days=1)).strftime(
                    "%Y-%m-%d"
                )
                day_before_items = cur.execute(
                    """
                    SELECT * FROM reminders WHERE date_next == ?""",
                    (dat,),
                ).fetchall()
                for item in day_before_items:
                    messages += f"\u2022 Due tomorrow: {item[1]}\n"
            # check whether user wants 'week before' notificatons
            if user_data[1]:
                dat = (datetime.today() + timedelta(days=7)).strftime(
                    "%Y-%m-%d"
                )
                week_before_items = cur.execute(
                    """
                    SELECT * FROM reminders WHERE date_next == ?""",
                    (dat,),
                ).fetchall()
                for item in week_before_items:
                    messages += f"\u2022 Due in 7 days: {item[1]}\n"
            # create notifications window only if there are messages
            if len(messages) > 0:
                # remove the last /n from messages
                messages = messages[:-1]
                NofificationsPopup(
                    self,
                    title="Items Coming Due",
                    message=messages,
                    x_offset=310,
                    y_offset=400,
                )
        #######################################
        # end notifications for upcoming events
        #######################################

    #################################
    # commands for left side buttons
    # create top level window for entry of data for new item
    def create_new(self):
        # remove any existing toplevels
        remove_toplevels(self)

        # create new toplevel
        top = TopLvl(self, "New Item")
        top.date_last_entry.insert(0, date.today())

        # get_date_cmd calls get date (calendar pop-up)
        def get_date_cmd(event):
            get_date(top.date_last_entry, top)

        # bind click in date_last_entry to get_date_cmd
        top.date_last_entry.bind("<1>", get_date_cmd)

        # function to save new item to database
        def save_item():
            # save_btn.config(state="disabled")
            con = get_con()
            cur = con.cursor()

            # validate inputs
            if not top.description_entry.get():
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Item cannot be blank.",
                )
                return

            # check for duplicate item
            result = cur.execute("""SELECT * FROM reminders""")
            for item in result.fetchall():
                if item[1] == top.description_entry.get():
                    InfoMsgBox(
                        self,
                        "Invalid Input",
                        "There is already an item with that description."
                        + " Try again.",
                    )
                    return

            if not valid_frequency(top.frequency_entry.get()):
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Frequency requires a numeric input.",
                )
                return

            if not top.date_last_entry.get():
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Please select a date for last.",
                )
                return

            if not top.period_combobox.get():
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Please select a period.",
                )
                return

            # calculate date_next
            date_last = top.date_last_entry.get()
            frequency = int(top.frequency_entry.get())
            period = top.period_combobox.get()
            date_next = date_next_calc(date_last, frequency, period)

            data_get = (
                top.description_entry.get(),
                frequency,
                top.period_combobox.get(),
                date_last,
                date_next,
                top.note_entry.get(),
            )
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
            refresh(self)

            # set view_label message and color
            check_expired(self)

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

    def pending(self):
        self.view_current = True
        data = cur.execute("""
            SELECT * FROM reminders
            WHERE date_next >= DATE('now', 'localtime')
            ORDER BY date_next ASC, description ASC
        """)
        for item in self.tree.get_children():
            self.tree.delete(item)
        insert_data(self, data)

        # set view_label message and color
        check_expired(self)

        remove_toplevels(self)
        self.refreshed = True
        self.tree.focus()

    def view_all(self):
        self.view_current = False
        data = cur.execute("""
            SELECT * FROM reminders
            ORDER BY date_next ASC, description ASC
        """)
        for item in self.tree.get_children():
            self.tree.delete(item)
        insert_data(self, data)

        # set view_label message and color
        check_expired(self)

        remove_toplevels(self)
        self.refreshed = True
        self.focus_set()
        self.tree.focus_set()

    def quit_program(self):
        self.destroy()

    # end commands for left side buttons
    ####################################

    #################################
    # commands for right side buttons
    def backup(self):
        answer = YesNoMsgBox(
            self,
            "Backup",
            "The current backup will be overwritten. Are you sure?",
            x_offset=600,
        )
        if answer.get_response():
            shutil.copy2(db_path, db_bak_path)
        else:
            return

    def restore(self):
        answer = YesNoMsgBox(
            self,
            "Restore",
            "Any current data will be overwritten. Are you sure?",
            x_offset=600,
        )
        if answer.get_response():
            shutil.copy2(db_bak_path, db_path)
            refresh(self)
            check_expired(self)
        else:
            return

    def delete_all(self):
        answer = YesNoMsgBox(
            self,
            "Delete All",
            "This will delete all data. Are you sure?",
            x_offset=600,
        )
        if answer.get_response():
            cur.execute("DELETE FROM reminders")
            con.commit()
            refresh(self)
            check_expired(self)
        else:
            return

    def notifications(self):
        # initialize user table if empty
        initialize_user()
        # check to see if user has a phone number; i.e., already receiving
        # notifications
        phone_number = cur.execute("SELECT * FROM user").fetchone()[0]
        if phone_number is None:
            response = YesNoMsgBox(
                self,
                title="Notifications",
                message="Would you like to to be notified by text "
                + "when your items are coming due?",
                x_offset=600,
            )
            # if user opts to receive notifications, get user data
            if response.get_response():
                get_user_data(self)
        # if user opts out of notifications, delete user's data
        else:
            response3 = YesNoMsgBox(
                self,
                title="Notifications",
                message="Do you want to continue receiving text"
                + " notifications?",
                x_offset=600,
            )
            if not response3.get_response():
                InfoMsgBox(
                    self,
                    "Notifications",
                    "You have opted out of text notifications."
                    + " Texts will no longer be sent.",
                    x_offset=600,
                )
                cur.execute("DELETE FROM user")
                con.commit()
            else:
                response4 = YesNoMsgBox(
                    self,
                    title="Notifications",
                    message="Do you want to change the phone number or"
                    + " notification frequency?",
                    x_offset=600,
                )
                if response4.get_response():
                    get_user_data(self)

    # end commands for right side buttons
    #####################################

    # manage row selection in treeview
    def on_treeview_selection_changed(self, event):  # noqa: PLR0915
        # abort if the selection change was after a refresh
        if self.refreshed:
            self.refreshed = False
            return

        selected_item = self.tree.focus()
        remove_toplevels(self)

        # create toplevel
        top = TopLvl(self, "Edit Selection")

        # capture id and description fields of the selected item
        id = self.tree.item(selected_item)["values"][0]
        original_description = self.tree.item(selected_item)["values"][1]

        # populate entries with data from the selection
        top.description_entry.insert(
            0, self.tree.item(selected_item)["values"][1]
        )
        top.frequency_entry.insert(
            0, self.tree.item(selected_item)["values"][2]
        )

        # use index function to determine index of the period_combobox value
        indx = top.period_list.index(
            self.tree.item(selected_item)["values"][3]
        )
        # set the combobox value using current function
        top.period_combobox.current(indx)
        top.date_last_entry.insert(
            0, self.tree.item(selected_item)["values"][4]
        )
        top.note_entry.insert(0, self.tree.item(selected_item)["values"][6])

        # get_date_cmd calls get date (calendar pop-up)
        def get_date_cmd(self):
            get_date(top.date_last_entry, top)

        # bind click in date_last_entry to get_date_cmd
        top.date_last_entry.bind("<1>", get_date_cmd)

        # update database
        def update_item():
            # validate inputs
            if not top.description_entry.get():
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Item cannot be blank.",
                )
                return

            if not valid_frequency(top.frequency_entry.get()):
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Frequency requires a numeric input.",
                )
                return

            if not top.date_last_entry.get() or not top.period_combobox.get():
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Please select a period and a last date.",
                )
                return

            # check for duplicate description
            result = cur.execute("""SELECT * FROM reminders""")
            for item in result.fetchall():
                if (
                    # item[1] is the selected description
                    item[1] == top.description_entry.get()
                    # duplicate OK if just changing other parameters
                    # item[0] is the selected id
                    and not item[0] == id
                ):
                    # reset original description
                    top.description_entry.delete(0, tk.END)
                    top.description_entry.insert(0, original_description)
                    InfoMsgBox(
                        self,
                        "Invalid Input",
                        "There is already an item with that description."
                        + " Try again.",
                    )
                    return

            # calculate date_next
            date_last = top.date_last_entry.get()
            frequency = int(top.frequency_entry.get())
            period = top.period_combobox.get()
            date_next = date_next_calc(date_last, frequency, period)

            cur.execute(
                """
                UPDATE reminders
                SET (
                description, frequency, period, date_last, date_next, note) =
                    (?, ?, ?, ?, ?, ?)
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

            # set view_label message and color
            check_expired(self)

            remove_toplevels(self)
            refresh(self)

        # delete item from database
        def delete_item():
            id = self.tree.item(selected_item)["values"][0]
            cur.execute(
                """
                DELETE FROM reminders
                WHERE id = ?""",
                (id,),
            )
            con.commit()
            refresh(self)

            # set view_label message and color
            check_expired(self)

            remove_toplevels(self)
            self.focus()
            self.tree.focus_set()

        def cancel():
            remove_toplevels(self)

        ttk.Button(top, text="Update", command=update_item).grid(
            row=2, column=1, pady=(15, 0), sticky="w"
        )

        ttk.Button(top, text="Delete", command=delete_item).grid(
            row=2, column=3, pady=(15, 0), sticky="w"
        )

        ttk.Button(top, text="Cancel", command=cancel).grid(
            row=2, column=5, pady=(15, 0), sticky="w"
        )


if __name__ == "__main__":
    app = App()
    app.mainloop()
