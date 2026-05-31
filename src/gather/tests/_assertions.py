# Shared assertions for the test suite.

import io

from hamcrest import assert_that, contains_string


def assert_stdout_contains(stream: io.StringIO, substring: str) -> None:
    """Assert that captured stdout contains a substring.

    Args:
        stream: the captured stdout buffer.
        substring: the text expected to appear in it.
    """
    assert_that(stream.getvalue(), contains_string(substring))
