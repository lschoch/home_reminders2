from loguru import logger  # noqa: F401

from business import categorize_reminders, get_expected, get_test_reminders


def test_categorize_reminder():
    reminders = get_test_reminders()
    # Specify expected result based on due dates of the test reminders
    expected = get_expected()
    logger.info(f"expected: {expected}")

    # Check function result when reminders is None.
    assert categorize_reminders(None) == ([], [], [], [])
    result = categorize_reminders(reminders)
    # Check that result exists.
    assert result
    assert result == expected
    # Check that the random reminder does not appear in result.
    assert "test5" not in result
