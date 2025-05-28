import os
import tkinter as tk
from datetime import datetime
from tkinter import ttk

from loguru import logger
from PIL import Image, ImageTk

from business import (
    create_database,
    date_check,
    get_user_data,
    insert_data,
    notifications_popup,
    refresh,
)
from classes import InfoMsgBox
from constants import WINDOW_GEOMETRY
from services import ReminderService
from ui_logic import (
    create_left_side_buttons,
    create_legend,
    create_menu_bar,
    create_searchbar,
    create_tree_widget,
)

# tracemalloc.start()

""" # create splash screen
if "_PYI_SPLASH_IPC" in os.environ and importlib.util.find_spec("pyi_splash"):
    import pyi_splash  # type: ignore

    pyi_splash.update_text("UI Loaded ...")
    pyi_splash.close()
    print("Splash screen closed.") """


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
        self.geometry(WINDOW_GEOMETRY)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.rowconfigure(0, minsize=140)

        # create variable to prevent calling treeview_on_selection_changed
        # after refresh
        self.refreshed = False

        # flag to track whether coming from view_all or view_current
        self.view_current = False

        # create database if it does not exist and retrieve data
        create_database(self)
        reminders = ReminderService.get_reminders(self, self.view_current)
        data = reminders if reminders else None

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

        # insert image
        try:
            house_img = ImageTk.PhotoImage(Image.open(self.ico_path))
            self.house_img_lbl = tk.Label(self, image=house_img)
            self.house_img_lbl.image = house_img
            self.house_img_lbl.grid(row=0, column=0, sticky="ns")
        except FileNotFoundError:
            logger.warning(
                f"Warning: Image not found at {self.ico_path}. Skipping "  # noqa: G004
                "image display."
            )

        # Create legend for colors in treeview.
        create_legend(self)
        # Create treeview to display data.
        self.tree = create_tree_widget(self)
        # Add reminders in the database to the treeview.
        if data:
            insert_data(self, data)
            refresh(self)
        else:
            logger.info("No reminders found to display.")
            InfoMsgBox(self, "Notice", "No reminders found.")

        # Add search bar
        create_searchbar(self)

        # Periodically check for notifications, if user has opted in to receive
        # them.
        user_data = get_user_data(self).fetchone()
        # user_data.fetchone()[0] = phone number. If present, user has opted to
        # receive notifications.
        if user_data:
            if user_data[0]:
                notifications_popup(self)

        # Monitor for date change.
        date_check(self)
        # Select the last item in the treeview. This will get focus into the
        # treeview but not interfere with the highlighting at the top of the
        # tree. Note: treeview will not accept focus at this point because the
        # notifications popup is open. This is a known issue with tkinter.
        if self.tree.get_children():
            last_index = len(self.tree.get_children()) - 1
            self.tree.selection_set(self.tree.get_children()[last_index])

    # end init
    ###############################################################


if __name__ == "__main__":
    app = App()
    app.focus_force()  # So that the app is on top at startup.
    app.mainloop()
