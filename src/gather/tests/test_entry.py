"""Test entrypoint."""

import argparse
import contextlib
import io
import logging
import sys
import unittest
from typing import Iterator, Sequence

from hamcrest import assert_that, contains_string, equal_to

from .. import entry

ENTRY_DATA = entry.EntryData.create("test_dunder_main")


@ENTRY_DATA.register(name="fake")
def _fake(args: argparse.Namespace) -> None:
    print("hello")


@contextlib.contextmanager
def _temporary_argv(argv: Sequence[str]) -> Iterator[None]:
    """Temporarily replace ``sys.argv``.

    ``dunder_main`` reads the process-global ``sys.argv``, so the entry path
    can only be exercised by swapping it out and restoring it afterwards.

    Args:
        argv: the argv to install for the duration of the context.

    Yields:
        Nothing; ``sys.argv`` is restored on exit.
    """
    original = sys.argv
    sys.argv = list(argv)
    try:
        yield
    finally:
        sys.argv = original


class DunderMainTest(unittest.TestCase):
    """Test dunder_main."""

    def test_failed_import(self) -> None:
        """Function fails if the name is not __main__."""
        with self.assertRaises(ImportError):
            entry.dunder_main(
                globals_dct=dict(__name__="some_name"),
                command_data=ENTRY_DATA,
                logger=logging.Logger("nonce"),
            )

    def test_run_command(self) -> None:
        """The fake command is called when the command line specifies it."""
        logger = logging.Logger("nonce")
        stream = io.StringIO()
        with _temporary_argv(["test", "fake"]), contextlib.redirect_stdout(stream):
            entry.dunder_main(
                globals_dct=dict(__name__="__main__"),
                logger=logger,
                command_data=ENTRY_DATA,
            )
        assert_that(stream.getvalue(), contains_string("hello"))  # noqa: SLD801

    def test_with_prefix(self) -> None:
        """An explicit prefix overrides the default."""
        ed = entry.EntryData.create("test_dunder_main", prefix="thing")
        assert_that(ed.prefix, equal_to("thing"))
