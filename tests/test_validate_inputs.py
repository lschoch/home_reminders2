import tkinter as tk  # noqa: F401

import pytest
from loguru import logger  # noqa: F401

from business import validate_inputs
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
                "description": "test1",  # Duplicate description
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
                "frequency": "2",
                "date_last": "",  # Empty date_last
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "-1",  # Negative frequency
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "invalid-date",  # Invalid date format
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "",  # All fields empty
                "frequency": "",
                "date_last": "",
                "period": "",
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

    if expected:
        assert validate_inputs(app, top, 0)
    else:
        assert not validate_inputs(app, top, 0)
