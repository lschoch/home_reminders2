import importlib
import os
import sqlite3
import tkinter as tk
from datetime import datetime
from tkinter import END, ttk

from icecream import ic  # noqa: F401
from PIL import Image, ImageTk

from business_logic import (
    create_tree_widget,
    date_check,
    date_next_calc,
    get_con,
    get_data,
    get_date,
    get_db_paths,
    insert_data,
    notifications_popup,
    refresh,
    remove_toplevels,
    validate_inputs,
)
from classes import InfoMsgBox, TopLvl, YesNoMsgBox
from ui_logic import (
    create_left_side_buttons,
    create_legend,
    create_menu_bar,
)

# tracemalloc.start()

# create splash screen
if "_PYI_SPLASH_IPC" in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash  # type: ignore

    pyi_splash.update_text("UI Loaded ...")
    pyi_splash.close()
    print("Splash screen closed.")

# get paths to database files
paths = get_db_paths()
# create database if it does not exist and retrieve data
data = get_data(paths[0])


# create the main window
class App(tk.Tk):
    def __init__(self, **kw):  # noqa: C901, PLR0915
        super().__init__(**kw)

        # get path to title bar icon
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.ico_path = os.path.join(base_dir, "images", "icons8-home-80.png")
        self.title("Home Reminders")
        # self.wm_overrideredirect(True)
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

        self.view_lbl_msg = tk.StringVar()
        self.view_lbl_color = tk.StringVar()
        self.expired_lbl_msg = tk.StringVar()
        self.todays_date_var = tk.StringVar()

        create_menu_bar(self)
        create_left_side_buttons(self)

        # set value of today's date variable
        self.todays_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        # create today's date label and set value to today_date_var
        self.today_is_lbl = tk.Label(
            self,
            text=f"Today is {self.todays_date_var.get()}",
            foreground="black",
            font=("Helvetica", 24),
        )
        self.today_is_lbl.grid(row=0, column=1, pady=(10, 0), sticky="n")

        # create viewing label and set text
        self.view_lbl = ttk.Label(
            self,
            textvariable=self.view_lbl_msg,
            background=self.view_lbl_color.get(),
            font=("Arial", 18),
        )
        self.view_lbl.grid(row=0, column=1, pady=(0, 45), sticky="s")

        # add search bar
        self.search_lbl = ttk.Label(
            self,
            text="Search:",
            font=("Arial", 14),
            background="#ececec",  # self.view_lbl_color.get(),
        )
        self.search_lbl.grid(row=0, column=1, padx=315, pady=10, sticky="sw")
        search_var = tk.StringVar()
        search_entry = ttk.Entry(
            self, textvariable=search_var, width=30, font=("Arial", 14)
        )
        search_entry.grid(
            row=0, column=1, ipadx=4, padx=(0, 315), pady=10, sticky="se"
        )

        def search_treeview():
            query = search_var.get().lower()
            for item in self.tree.get_children():
                values = self.tree.item(item, "values")
                if query in str(values).lower():
                    self.tree.selection_set(item)
                    # remove any existing toplevels
                    remove_toplevels
                    # scroll to the first matching item
                    self.tree.see(item)
                    self.tree.focus(item)
                    break

        search_entry.bind("<Return>", lambda e: search_treeview())

        # insert image
        try:
            house_img = ImageTk.PhotoImage(Image.open(self.ico_path))
            self.house_img_lbl = tk.Label(self, image=house_img)
            self.house_img_lbl.image = house_img
            self.house_img_lbl.grid(row=0, column=0, sticky="ns")
        except FileNotFoundError:
            pass

        # create legend for colors in treeview
        create_legend(self)
        # create treeview to display data
        self.tree = create_tree_widget(self)
        # add data to treeview
        insert_data(self, data)
        refresh(self)
        notifications_popup(self)
        date_check(self)

        # on startup, select the last item in the treeview - to get focus
        # in treeview without interfering with item highlighting
        last_index = len(self.tree.get_children()) - 1
        self.tree.selection_set(self.tree.get_children()[last_index])

    # end init
    ###############################################################

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

        # capture id of the selected item
        id = self.tree.item(selected_item)["values"][0]

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

        # bind click in date_last_entry to get_date
        top.date_last_entry.bind(
            "<1>", lambda e: get_date(top.date_last_entry, top)
        )

        # update database
        def update_item():
            # validate inputs before saving, exit if validation fails
            validate = validate_inputs(self, top, new=False, id=id)
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

        # delete item from database
        ""

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
            try:
                with get_con() as con:
                    cur = con.cursor()
                    cur.execute(
                        """
                        DELETE FROM reminders
                        WHERE id = ?""",
                        (id,),
                    )
                    con.commit()
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                InfoMsgBox(self, "Error", "Failed to update the database.")
            refresh(self)
            remove_toplevels(self)
            self.focus()
            self.tree.focus_set()

        ""

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
