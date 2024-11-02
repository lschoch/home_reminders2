import sqlite3
import tkinter as tk
import os
import shutil
import sys
from datetime import date
from tkinter import messagebox, ttk

from PIL import Image, ImageTk

from classes import TopLvl
from functions import (
    check_expired,
    create_tree_widget,
    date_next_calc,
    get_con,
    get_date,
    insert_data,
    refresh,
    remove_toplevels,
    valid_frequency,
)

# connect to database and create cursor
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    base_dir = sys._MEIPASS
else:
    # Running as a normal script
    base_dir = os.path.dirname(os.path.abspath(__file__))

db_path = os.path.join(base_dir, "home_reminders.db")
db_bak_path = os.path.join(base_dir, "home_reminders.bak")
con = sqlite3.connect(db_path)
cur = con.cursor()


# create table if it doesn't exist
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

# select data for display, bring NULLs forward so they don't get lost
data = cur.execute("""
    SELECT * FROM reminders
    WHERE date_next >= DATE('now', 'localtime')
    ORDER BY date_next ASC, description ASC
""")


# create the main window
class App(tk.Tk):
    def __init__(self, **kw):
        super().__init__(**kw)

        # get path to title bar icon
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            base_dir = sys._MEIPASS
        else:
            # Running as a normal script
            base_dir = os.path.dirname(os.path.abspath(__file__))

        """ ################################
        if getattr(sys, 'frozen', False):
            EXE_LOCATION = os.path.dirname( sys.executable ) # cx_Freeze frozen
        else:
            EXE_LOCATION = os.path.dirname( os.path.realpath( __file__ ) ) # Other packers
        ################################ """

        self.ico_path = os.path.join(base_dir, "images", "icons8-home-80.png")

        self.title("Home Reminders")
        ico = Image.open(self.ico_path)
        photo = ImageTk.PhotoImage(ico)
        self.wm_iconphoto(True, photo)
        self.geometry("1120x400+3+30")
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

        # create main screen
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
            foreground="red",
            font=("Helvetica", 24),
        )
        self.today_is_lbl.grid(row=0, column=1, pady=(10, 0), sticky="n")

        # insert images
        img_r = ImageTk.PhotoImage(
            Image.open(
                "/Users/larry/python/reminders/images/icons8-home-80.png"
            )
        )
        img_l = ImageTk.PhotoImage(
            Image.open(
                "/Users/larry/python/reminders/images/icons8-home-80.png"
            )
        )
        """ self.img_lbl_r = tk.Label(self, image=img_r)
        self.img_lbl_r.image = img_r
        self.img_lbl_r.grid(row=0, column=3, padx=(47,0), sticky='w') """
        self.img_lbl_l = tk.Label(self, image=img_l)
        self.img_lbl_l.image = img_l
        self.img_lbl_l.grid(row=0, column=0, sticky='ns')

        ####################################
        # create legend
        self.legend_frame = tk.Frame(
            # self, highlightbackground="black", highlightthickness=1
            self
        )
        self.legend_frame.grid(
            row=0, column=3, pady=(0, 40), sticky='s')

        tk.Label(
            self.legend_frame,
            text="Legend:",
            justify="center",
            font=("Arial bold", 14),
            foreground="black",
            background="#ececec",
        ).grid(row=0, column=0, pady=(5, 0), columnspan=2)

        tk.Label(
            self.legend_frame,
            text="  ",
            width=2,
            background="lightblue",
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
            row=1, column=3, padx=(20, 0), pady=(45, 0), sticky='n'
        )
        ttk.Button(self, text='Restore', command=self.restore).grid(
            row=1, column=3, padx=(20, 0), pady=(95, 0), sticky='n'
        )
        ttk.Button(self, text="Delete All", command=self.delete_all).grid(
            row=1, column=3, padx=(20, 0), pady=(145, 0), sticky='n')
        # end right side buttons
        ####################################

        # create treeview to display data
        self.tree = create_tree_widget(self)

        # add data to treeview
        insert_data(self, data)

        # set view_label message and color
        check_expired(self)

        self.focus_set()
        self.tree.focus_set()

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
            con = get_con()
            cur = con.cursor()

            # validate inputs
            if not top.description_entry.get():
                messagebox.showinfo(
                    "Invalid Input", "Item cannot be blank."
                )
                return
            
            if not valid_frequency(top.frequency_entry.get()):
                messagebox.showinfo(
                    "Invalid Input", "Frequency requires a numeric input."
                )
                return

            if not top.date_last_entry.get() or not top.period_combobox.get():
                messagebox.showinfo(
                    "Invalid Input", "Please select a period and a date_last."
                )
                return
            

            # check for duplicate item
            result = cur.execute("""SELECT * FROM reminders""")
            for item in result.fetchall():
                if item[1] == top.description_entry.get():
                    messagebox.showinfo(
                        "Invalid Input",
                        """There is already an item with that description.\n
                        Try again.""",
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

            top.destroy()
            self.tree.focus()

        def cancel():
            # remove_toplevels(self)
            top.destroy()
            self.tree.focus()

        ttk.Button(top, text="Save", command=save_item).grid(
            row=2, column=1, padx=(33, 0), pady=(15, 0), sticky="w"
        )

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
        self.focus_set()
        self.tree.focus_set()

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

    ####################################
    # functions for right side buttons
    def backup(self):
        answer = messagebox.askyesno("Backup", "The current backup will be overwritten. Are you sure?")
        if answer:
            shutil.copy2(db_path, db_bak_path)
        else:
            return
        
    def restore(self):
        answer = messagebox.askyesno("Restore", "Any current data will be overwritten. Are you sure?")
        if answer:
            shutil.copy2(db_bak_path, db_path)
            refresh(self)
            check_expired(self)
        else:
            return
        
    def delete_all(self):
        answer = messagebox.askyesno("Delete All", "This will delete all data. Are you sure?")
        if answer:
            cur.execute("DELETE FROM reminders")
            con.commit()
            refresh(self)
            check_expired(self)
        else:
            return
    # end functions for right side buttons

    # create toplevel to manage row selection
    def on_treeview_selection_changed(self, event):
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
                messagebox.showinfo(
                    "Invalid Input", "Item cannot be blank."
                )
                return
            
            if not valid_frequency(top.frequency_entry.get()):
                messagebox.showinfo(
                    "Invalid Input", "Frequency requires a numeric input."
                )
                return

            if not top.date_last_entry.get() or not top.period_combobox.get():
                messagebox.showinfo(
                    "Invalid Input", "Please select a period and a date_last."
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
                    messagebox.showinfo(
                        "Invalid Input",
                        """There is already an item with that description.\n
                        Try again.""",
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
