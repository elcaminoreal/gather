# Shared assertions for the test suite.

import io
from typing import Mapping

from hamcrest import assert_that, contains_string


def assert_stdout_contains(stream: io.StringIO, substring: str) -> None:
    """Assert that captured stdout contains a substring.

    Args:
        stream: the captured stdout buffer.
        substring: the text expected to appear in it.
    """
    assert_that(stream.getvalue(), contains_string(substring))


def assert_file_contents(
    contents: Mapping[str, str], expected: Mapping[str, str]
) -> None:
    """Assert each expected file holds its expected text.

    Args:
        contents: file name to file text, as produced by a command.
        expected: file name to the text each file must contain.
    """
    missing = {name: contents.get(name) for name in expected}
    assert missing == dict(expected), (missing, dict(expected))


def assert_file_absent(contents: Mapping[str, str], name: str) -> None:
    """Assert a directory does not contain a named file.

    Args:
        contents: file name to file text, as produced by a command.
        name: the file name expected to be absent.
    """
    assert name not in contents, name
