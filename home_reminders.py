import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk

# from icecream import ic  # noqa: F401
from PIL import Image, ImageTk

from business_logic import (
    create_database,
    date_check,
    fetch_reminders,
    insert_data,
    notifications_popup,  # noqa: F401
    refresh,
)
from ui_logic import (
    create_left_side_buttons,
    create_legend,
    create_menu_bar,
    create_tree_widget,
    remove_toplevels,
)

# tracemalloc.start()

""" # create splash screen
if "_PYI_SPLASH_IPC" in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash  # type: ignore

    pyi_splash.update_text("UI Loaded ...")
    pyi_splash.close()
    print("Splash screen closed.") """

""" # get paths to database files
paths = get_db_paths() """


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

        # create database if it does not exist and retrieve data
        create_database(self)
        data = fetch_reminders(self)

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
        # add reminders to the treeview
        insert_data(self, data)
        refresh(self)
        # Periodically check whether notifications are due.
        notifications_popup(self)
        # Monitor for date change.
        date_check(self)
        # On startup, select the last item in the treeview - to get focus into
        # the treeview without interfering with item highlighting at the top of
        # the list.
        last_index = len(self.tree.get_children()) - 1
        self.tree.selection_set(self.tree.get_children()[last_index])

    # end init
    ###############################################################


if __name__ == "__main__":
    app = App()
    app.focus_force()
    app.mainloop()
