## <img  src="images/icons8-home-40.png" alt="Home Reminders icon"> &nbsp;&nbsp;Home Reminders
Home Reminders is a Python script that was originally developed to track household tasks but it can also be used as a general purpose reminder tool. The application implements a graphical user interface using Tkinter and the main feature is a treeview table of reminder items, including the last date the item was performed and the next due date. The next due date is calculated based on information entered by the user. There is also an option for one-time (non-repeating) reminders. Items in the table are sorted by their due date, in ascending order.

Data is stored in a Sqlite database and this is stored in the Application Support folder of the user's computer. A backup copy of the database file can be created from within the application. At present, there is no cloud storage so the application data is confined to a specific device. The applicaton is packaged separately for Windows and Mac OS X. No other operating systems are supported at this time.
### Usage:
1. Selecting an item in the table produces a popup window for editing or deleting the item.
2. There is a button for adding a new item and a button for quitting the application.
3. The menu bar provides options for:
    a. opting in or out of notifications.
    b. viewing all items or just those that are pending.
    c. backing up, restoring or deleting all items.
### In the works:
1. Provide the user with the option to receive text reminders in addition to on screen notifications. 
2. Provide cloud storage so that the application data is not confined to one device.
3. Extend support to Linux.
