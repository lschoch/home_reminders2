import tkinter as tk

from loguru import logger

from business import error_handler
from classes import InfoMsgBox, TestError


def test_error_handler(caplog, reportlog):
    app = tk.Tk()
    msg = "This is the TestError message."

    # generate an error so that the error handler can be tested
    try:
        raise TestError(msg)
    except TestError:
        logger.info(TestError(msg))
        # Call the error handler function
        error_handler(app, msg)

        # Check if the error message is displayed in the InfoMsgBox
        for widget in app.winfo_children():
            if isinstance(widget, tk.Text) and type(widget) is InfoMsgBox:
                assert widget.get("1.0", tk.END) == f"{msg}"
        # Check if the error message is logged
        assert msg in caplog.text
