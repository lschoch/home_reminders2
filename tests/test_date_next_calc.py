import tkinter as tk

import pytest

from business import date_next_calc
from classes import TopLvl


@pytest.mark.parametrize(
    "date_last_entry, frequency_entry, period_combobox, expected",
    [
        ("2025-10-01", "1", "one-time", "2025-10-01"),
        ("2023-10-01", "1", "days", "2023-10-02"),
        ("2023-10-01", "2", "weeks", "2023-10-15"),
        ("2023-10-01", "1", "months", "2023-11-01"),
        ("2023-10-01", "1", "years", "2024-10-01"),
    ],
)
def test_date_next_calc(
    mocker, date_last_entry, frequency_entry, period_combobox, expected
):
    """
    Test the date_next_calc function using parametrization.
    """
    # Mock the TopLvl class.
    mocker = tk.Tk()
    top = TopLvl(mocker, "Test")
    # Initialize widgets that are set up in the TopLvl class. Date_next_calc
    # retrieves the values from these widgets to calculate the next date.
    top.date_last_entry.insert(0, date_last_entry)
    top.frequency_entry.insert(0, frequency_entry)
    top.period_combobox.insert(0, period_combobox)

    result = date_next_calc(top)
    assert result == expected
