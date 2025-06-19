import tkinter as tk  # noqa: F401

import pytest
from loguru import logger  # noqa: F401

from business import fetch_reminders, validate_inputs
from classes import TopLvl


@pytest.mark.parametrize(
    "inputs, expected",
    [
        # Valid input
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            True,
        ),
        (
            {
                "description": "test1",  # Duplicate description but this is an
                # update, so it should be valid.
                "frequency": "2",
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            True,
        ),
        # Invalid inputs
        (
            {
                "description": "",  # Empty description
                "frequency": "2",
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "",  # Empty frequency
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2.3",  # Non-integer frequency
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "202-01-01",  # Invalid date format
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "",  # No date_last
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "2025-01-01",
                "period": "invalid-period",  # Invalid period
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "2025-01-01",
                "period": "",  # Empty period
            },
            False,
        ),
    ],
)
def test_validate_inputs(inputs, expected, mocker):
    app = tk.Tk()
    app.view_current = False
    top = mocker.Mock(spec=TopLvl)
    top.description_entry = mocker.Mock()
    top.description_entry.get.return_value = inputs["description"]
    top.frequency_entry = mocker.Mock()
    top.frequency_entry.get.return_value = inputs["frequency"]
    top.date_last_entry = mocker.Mock()
    top.date_last_entry.get.return_value = inputs["date_last"]
    top.period_combobox = mocker.Mock()
    top.period_combobox.get.return_value = inputs["period"]

    # Get a reminder from the database to test this function.
    reminder = fetch_reminders(app, app.view_current).fetchone()
    logger.info(f"reminder: {reminder}")
    id = reminder[0]
    # description = reminder[1]

    # Simulate updating this existing reminder.
    if expected:
        assert validate_inputs(app, top, id)
    else:
        assert not validate_inputs(app, top, id)

    # TODOS:
    # 1. Determine how a new reminder is saved (vis a vis id) and test
    #    appropriately.
