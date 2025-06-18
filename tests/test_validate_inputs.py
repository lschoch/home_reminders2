import tkinter as tk

import pytest
from loguru import logger  # noqa: F401

from business import validate_inputs
from classes import TopLvl


@pytest.mark.parametrize(
    "inputs, expected",
    [
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
                "description": "",
                "frequency": "2",
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "",
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "-1",
                "date_last": "2025-01-01",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "test",
                "frequency": "2",
                "date_last": "invalid-date",
                "period": "weeks",
            },
            False,
        ),
        (
            {
                "description": "",
                "frequency": "",
                "date_last": "",
                "period": "",
            },
            False,
        ),
    ],
)
def test_validate_inputs(inputs, expected):
    app = tk.Tk()
    top = TopLvl(app, "Title")
    app.view_current = True
    top.description_entry.insert(0, inputs["description"])
    top.frequency_entry.insert(0, inputs["frequency"])
    top.date_last_entry.insert(0, inputs["date_last"])
    top.period_combobox.set(inputs["period"])
    logger.info(f"inputs: {inputs}; expected: {expected}")

    if expected:
        assert validate_inputs(app, top, 0)
    else:
        assert not validate_inputs(app, top, 0)
