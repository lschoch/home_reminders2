from business import appsupportdir


def test_appsupportdir():
    """
    Test the appsupportdir function.
    """
    result = appsupportdir()
    print(f"result: {result}")
    assert result == "/Users/larry/Library/Application Support"
