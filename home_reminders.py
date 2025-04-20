import importlib
import os
import shutil
import tkinter as tk
from datetime import date, datetime
from tkinter import END, Menu, ttk

from memory_profiler import profile
from PIL import Image, ImageTk

from business_logic import (
    appsupportdir,
    check_expired,
    create_tree_widget,
    date_next_calc,
    get_con,
    get_data,
    get_date,
    get_user_data,
    initialize_user,
    insert_data,
    notifications_popup,
    quit_program,
    refresh,
    refresh_date,
    remove_toplevels,
    valid_frequency,
)
from classes import InfoMsgBox, TopLvl, YesNoMsgBox

# tracemalloc.start()

# create splash screen
if "_PYI_SPLASH_IPC" in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash  # type: ignore

    pyi_splash.update_text("UI Loaded ...")
    pyi_splash.close()
    print("Splash screen closed.")

# create path to database and backup files
dir_path = os.path.join(appsupportdir(), "Home Reminders")
if not os.path.exists(dir_path):
    os.makedirs(dir_path)
db_path = os.path.join(dir_path, "home_reminders.db")
db_bak_path = os.path.join(dir_path, "home_reminders.bak")
# create database if it does not exist and retrieve data
data = get_data(db_path)


# create the main window
class App(tk.Tk):
    def __init__(self, **kw):  # noqa: C901, PLR0915
        super().__init__(**kw)

        # get path to title bar icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ico_path = os.path.join(base_dir, "images", "icons8-home-80.png")
        self.title("Home Reminders")
        # self.wm_overrideredirect(True)
        # self.wm_attributes('-type', 'splash')
        ico = Image.open(self.ico_path)
        photo = ImageTk.PhotoImage(ico)
        self.wm_iconphoto(True, photo)
        self.geometry("1140x393+3+3")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.rowconfigure(0, minsize=140)

        # create variable to prevent calling treeview_on_selection_changed
        # after refresh
        self.refreshed = False

        # flag to track whether coming from view_all or view_current
        self.view_current = False

        self.lbl_msg = tk.StringVar()
        self.lbl_color = tk.StringVar()
        self.expired_msg = tk.StringVar()
        self.date_var = tk.StringVar()

        ###############################################################
        # create menus
        self.option_add("*tearOff", False)

        def opt_in():
            # initialize user table if empty
            initialize_user()
            with get_con() as con:
                cur = con.cursor()
                # check to see if user has a phone number; i.e., already
                # receiving notifications
                phone_number = cur.execute("SELECT * FROM user").fetchone()[0]
            if phone_number is None:
                response = YesNoMsgBox(
                    self,
                    title="Notifications",
                    message="Would you like to to be notified by text "
                    + "when your items are coming due?",
                    x_offset=3,
                    y_offset=5,
                )
                # if user opts to receive notifications, get user data
                if response.get_response() == 1:
                    get_user_data(self)
                elif response.get_response == -1:
                    InfoMsgBox(
                        self,
                        "Notifications",
                        "You have opted out of text notifications."
                        + " Texts will no longer be sent.",
                        x_offset=3,
                        y_offset=5,
                    )
                    cur.execute("DELETE FROM user")
                    con.commit()
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
                if response1.get_response() == -1:
                    InfoMsgBox(
                        self,
                        "Notifications",
                        "You have opted out of text notifications."
                        + " Texts will no longer be sent.",
                        x_offset=3,
                        y_offset=5,
                    )
                    cur.execute("DELETE FROM user")
                    con.commit()
                elif response1.get_response() == 1:
                    response2 = YesNoMsgBox(
                        self,
                        title="Notifications",
                        message="""Do you want to change your notification
                         phone number or notification frequency?""",
                        x_offset=3,
                        y_offset=5,
                    )
                    if response2.get_response() == 1:
                        get_user_data(self)

        def opt_out():
            initialize_user()
            with get_con() as con:
                cur = con.cursor()
                # check to see if user has a phone number; i.e., already
                # receiving notifications
                phone_number = cur.execute("SELECT * FROM user").fetchone()[0]
            if phone_number is not None:
                response = YesNoMsgBox(
                    self,
                    title="Notifications",
                    message="""Do you want to stop receiving
                     text notifications?""",
                    x_offset=3,
                    y_offset=5,
                )
                if response.get_response() == 1:
                    InfoMsgBox(
                        self,
                        "Notifications",
                        "You have opted out of text notifications."
                        + " Texts will no longer be sent.",
                        x_offset=3,
                        y_offset=5,
                    )
                    with get_con() as con:
                        cur = con.cursor()
                        cur.execute("DELETE FROM user")
                        con.commit()
            else:
                InfoMsgBox(
                    self,
                    "Notifications",
                    "You are not currently receiving text notifications. "
                    + "Click opt-in to start.",
                    x_offset=3,
                    y_offset=5,
                )

        def preferences():
            initialize_user()
            # check to see if user has a phone number; i.e., already receiving
            # notifications
            with get_con() as con:
                cur = con.cursor()
                phone_number = cur.execute("SELECT * FROM user").fetchone()[0]
            if phone_number is not None:
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

        menubar = Menu(self)
        self.config(menu=menubar)

        notifications_menu = Menu(menubar)
        menubar.add_cascade(label="Notifications", menu=notifications_menu)
        notifications_menu.add_command(label="Opt-in", command=opt_in)
        notifications_menu.add_command(label="Opt-out", command=opt_out)
        notifications_menu.add_command(
            label="Preferences", command=preferences
        )

        view_menu = Menu(menubar)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Pending", command=self.pending)
        view_menu.add_command(label="All", command=self.view_all)

        data_menu = Menu(menubar)
        menubar.add_cascade(label="Data", menu=data_menu)
        data_menu.add_command(label="Backup", command=self.backup)
        data_menu.add_command(label="Restore", command=self.restore)
        data_menu.add_command(label="Delete All", command=self.delete_all)
        # end create menus
        ###############################################################

        ###############################################################
        # add left side buttons
        self.btn = ttk.Button(
            self, text="New Item", command=self.create_new
        ).grid(row=1, column=0, padx=20, pady=(20, 0), sticky="n")
        self.btn = ttk.Button(self, text="Quit", command=quit_program).grid(
            row=1, column=0, padx=20, pady=(60, 0), sticky="n"
        )
        # end left side buttons
        ###############################################################

        self.view_lbl = ttk.Label(
            self,
            textvariable=self.lbl_msg,
            background=self.lbl_color.get(),
            font=("Arial", 18),
        )
        self.view_lbl.grid(row=0, column=1, pady=(0, 45), sticky="s")

        self.expired_lbl = tk.Label(
            self,
            textvariable=self.expired_msg,
            background="yellow",
            borderwidth=1,
            relief="solid",
        )
        self.expired_lbl.grid(
            row=0, column=1, ipadx=4, ipady=4, pady=(10), sticky="s"
        )

        ###############################################################
        # insert image
        try:
            img_l = ImageTk.PhotoImage(Image.open(self.ico_path))
            self.img_lbl_l = tk.Label(self, image=img_l)
            self.img_lbl_l.image = img_l
            self.img_lbl_l.grid(row=0, column=0, sticky="ns")
        except FileNotFoundError:
            pass
        ###############################################################

        ###############################################################
        # create legend
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
        ttk.Label(
            self.legend_frame, text="pending - ", background="#ececec"
        ).grid(row=3, column=0, padx=(5, 0), pady=(5, 0), sticky="e")
        # end legend
        ###############################################################

        # create treeview to display data
        self.tree = create_tree_widget(self)

        # add data to treeview
        insert_data(self, data)

        # set view_label message and color
        check_expired(self)
        if self.tree.get_children():
            child_id = self.tree.get_children()[0]
            self.tree.focus(child_id)
        # self.tree.selection_set(child_id)

        # initialize date_var to today's date if not set
        if not self.date_var.get():
            try:
                self.date_var.set(datetime.now().strftime("%Y-%m-%d"))
            except Exception as e:
                print(f"Error initializing date_var: {e}")

        notifications_popup(self)
        refresh_date(self, data)

    # end init
    ###############################################################

    ###############################################################
    # commands for left side buttons
    # create top level window for entry of data for new item
    @profile
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

            # validate inputs
            if not top.description_entry.get():
                InfoMsgBox(
                    self,
                    "Invalid Input",
                    "Item cannot be blank.",
                )
                return

            # check for duplicate item
            with get_con() as con:
                cur = con.cursor()
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

            if top.period_combobox.get() == "one-time":
                frequency = "1"

            data_get = (
                top.description_entry.get(),
                frequency,
                top.period_combobox.get(),
                date_last,
                date_next,
                top.note_entry.get(),
            )
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

    @profile
    def pending(self):
        self.view_current = True
        with get_con() as con:
            cur = con.cursor()
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

    @profile
    def view_all(self):
        self.view_current = False
        with get_con() as con:
            cur = con.cursor()
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

    # end commands for left side buttons
    ###############################################################

    @profile
    def backup(self):
        answer = YesNoMsgBox(
            self,
            "Backup",
            "The current backup will be overwritten. Are you sure?",
            x_offset=3,
            y_offset=5,
        )
        if answer.get_response():
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

    @profile
    def restore(self):
        answer = YesNoMsgBox(
            self,
            "Restore",
            "All current data will be overwritten. Are you sure?",
            x_offset=3,
            y_offset=5,
        )
        if answer.get_response():
            shutil.copy2(db_bak_path, db_path)
            refresh(self)
            check_expired(self)
            InfoMsgBox(
                self,
                "Restore",
                "Data restored.",
                x_offset=3,
                y_offset=5,
            )
        else:
            return

    @profile
    def delete_all(self):
        answer = YesNoMsgBox(
            self,
            "Delete All",
            "This will delete all data. Are you sure?",
            x_offset=3,
            y_offset=5,
        )
        if answer.get_response():
            with get_con() as con:
                cur = con.cursor()
                cur.execute("DELETE FROM user")
                con.commit()
            refresh(self)
            check_expired(self)
            InfoMsgBox(
                self,
                "Delete All",
                "Data has been deleted.",
                x_offset=3,
                y_offset=5,
            )
        else:
            return

    """ @profile
    def notifications(self):
        # initialize user table if empty
        initialize_user()
        # check to see if user has a phone number; i.e., already receiving
        # notifications
        with get_con() as con:
            cur = con.cursor()
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
                        get_user_data(self) """

    # manage row selection in treeview
    @profile
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
            with get_con() as con:
                cur = con.cursor()
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
                # set frequency to 1 if period is "one-time"
                if top.period_combobox.get() == "one-time":
                    top.frequency_entry.delete(0, END)
                    top.frequency_entry.insert(0, "1")

                cur.execute(
                    """
                    UPDATE reminders
                    SET (
                    description, frequency, period, date_last, date_next, note)
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

            # set view_label message and color
            check_expired(self)

            remove_toplevels(self)
            refresh(self)

        # delete item from database
        @profile
        def delete_item():
            answer = YesNoMsgBox(
                self,
                "Delete Reminder",
                "Are you sure you want to delete  \
                    this reminder?",
            )
            if not answer.get_response():
                return
            id = self.tree.item(selected_item)["values"][0]
            with get_con() as con:
                cur = con.cursor()
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

        @profile
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
