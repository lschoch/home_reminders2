## <img  src="images/icons8-home-40.png" alt="Home Reminders icon"> &nbsp;&nbsp;Home Reminders
Home Reminders is a Python script that was originally developed to track household tasks (e.g., changing the furnace filter). It can also be used as a general purpose reminder tool. The application provides a table of items including the last date the item was performed and the date the item should be repeated. The repeat date is calculated based on data entered by the user. There is also a column for a note about each item (e.g., where replacement furnace filters can be obtained). Data is stored in a Sqlite database. This file is stored in the Application Support folder of the user's computer along with a backup copy of the database file that can be created from within the application. At present, there is no cloud storage so the application data is confined to a specific device. The applicaton is packaged separately for Windows and Mac OS X. No other operating systems are supported at this time.
### Notes:
1. Selecting a particular item sometimes requires a second click.
2. Items in the table are sorted by the date they are to be performed, in ascending order.
### Planned improvements:
1. Provide the user with the option to receive text reminders.
2. Provide search capability.
3. Provide cloud storage so that the application data is not confined to one device.
4. Extend support to Linux.
