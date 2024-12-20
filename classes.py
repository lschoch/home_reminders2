import tkinter as tk
from tkinter import ttk


# create toplevel
class TopLvl(tk.Toplevel):
    def __init__(self, master, title):
        super().__init__(master)
        self.title(title)
        self.config(padx=20, pady=20)
        x = master.winfo_x()
        y = master.winfo_y()
        self.geometry("+%d+%d" % (x + 156, y + 410))

        # create list of values for period_combobox that will be be accessed
        # outside the combobox configuration
        self.period_list = ["days", "weeks", "months", "years"]

        # create entry labels and widgets for the top level
        ttk.Label(self, text="item", background="#ececec").grid(
            row=0, column=0, padx=(0, 5), pady=(0, 15), sticky="e"
        )
        self.description_entry = ttk.Entry(self)
        self.description_entry.grid(
            row=0, column=1, padx=(0, 15), pady=(0, 15)
        )

        ttk.Label(self, text="frequency", background="#ececec").grid(
            row=0, column=2, padx=5, pady=(0, 15), sticky="e"
        )
        self.frequency_entry = ttk.Entry(self)
        self.frequency_entry.grid(row=0, column=3, padx=(0, 15), pady=(0, 15))

        ttk.Label(self, text="period", background="#ececec").grid(
            row=0, column=4, padx=5, pady=(0, 15), sticky="e"
        )
        self.period_combobox = AutocompleteCombobox(self)
        self.period_combobox.set_list(self.period_list)
        self.period_combobox.grid(row=0, column=5, pady=(0, 15))
        self.period_combobox.grid(row=0, column=5, pady=(0, 15))

        ttk.Label(self, text="last", background="#ececec").grid(
            row=1, column=0, padx=(0, 5), pady=(0, 15), sticky="e"
        )
        self.date_last_entry = ttk.Entry(self)
        self.date_last_entry.grid(row=1, column=1, padx=(0, 15), pady=(0, 15))

        ttk.Label(self, text="note", background="#ececec").grid(
            row=1, column=2, padx=(0, 5), pady=(0, 15), sticky="e"
        )
        self.note_entry = ttk.Entry(self, width=48)
        self.note_entry.grid(
            row=1,
            column=3,
            columnspan=3,
            padx=(0, 15),
            pady=(0, 15),
            sticky="w",
        )


class AutocompleteCombobox(ttk.Combobox):
    def set_list(self, completion_list):
        """Use completion list for the drop down selection menu, arrows move
        through menu."""
        self._completion_list = completion_list
        self._hits = []
        self._hit_index = 0
        self.position = 0
        self.bind("<KeyRelease>", self.handle_keyrelease)
        self["values"] = self._completion_list  # Setup our popup menu

    def autocomplete(self, delta=0):
        """Autocomplete the Combobox, delta may be 0/1/-1 to cycle through
        possible hits"""
        # need to delete selection otherwise we would fix the current position
        if delta:
            self.delete(self.position, tk.END)
        else:  # set position to end so selection starts where textentry ended
            self.position = len(self.get())
        # collect hits
        _hits = []
        for element in self._completion_list:
            if element.lower().startswith(
                self.get().lower()
            ):  # Match case insensitively
                _hits.append(element)
        # if we have a new hit list, keep this in mind
        if _hits != self._hits:
            self._hit_index = 0
            self._hits = _hits
        # only allow cycling if we are in a known hit list
        if _hits == self._hits and self._hits:
            self._hit_index = (self._hit_index + delta) % len(self._hits)
        # now finally perform the auto completion
        if self._hits:
            self.delete(0, tk.END)
            self.insert(0, self._hits[self._hit_index])
            # self.select_range(self.position, tk.END)
            # self.select_clear()
            self.config(state="readonly")

    def handle_keyrelease(self, event):
        """Event handler for the keyrelease event on this widget"""
        if event.keysym == "BackSpace":
            self.delete(self.index(tk.INSERT), tk.END)
            self.position = self.index(tk.END)
        if event.keysym == "Left":
            if self.position < self.index(tk.END):  # delete the selection
                self.delete(self.position, tk.END)
            else:
                self.position = self.position - 1  # delete one character
                self.delete(self.position, tk.END)
        if event.keysym == "Right":
            self.position = self.index(tk.END)  # go to end (no selection)
        if len(event.keysym) == 1:
            self.autocomplete()
        # No need for up/down, we'll jump to the popup
        # list at the position of the autocompletion


def test(test_list):
    """Run a mini application to test the AutocompleteEntry Widget."""
    root = tk.Tk(className=" AutocompleteEntry demo")
    """ entry = AutocompleteEntry(root)
    entry.set_completion_list(test_list)
    entry.pack()
    entry.focus_set() """
    combo = AutocompleteCombobox(root)
    combo.set_completion_list(test_list)
    combo.pack()
    combo.focus_set()
    # I used a tiling WM with no controls, added a shortcut to quit
    root.bind("<Control-Q>", lambda event=None: root.destroy())
    root.bind("<Control-q>", lambda event=None: root.destroy())
    root.mainloop()


if __name__ == "__main__":
    test_list = (
        "apple",
        "banana",
        "CranBerry",
        "dogwood",
        "alpha",
        "Acorn",
        "Anise",
    )
    test(test_list)
