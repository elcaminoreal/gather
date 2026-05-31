"""Test entrypoint"""
import argparse
import io
import logging
import unittest
from unittest import mock

from hamcrest import assert_that, contains_string, equal_to

from .. import entry

ENTRY_DATA = entry.EntryData.create("test_dunder_main")


@ENTRY_DATA.register(name="fake")
def _fake(args: argparse.Namespace) -> None:
    print("hello")


class DunderMainTest(unittest.TestCase):

    """Test dunder_main"""

    def test_failed_import(self) -> None:
        """
        Function fails if the name is not __main__
        """
        with self.assertRaises(ImportError):
            entry.dunder_main(
                globals_dct=dict(__name__="some_name"),
                command_data=ENTRY_DATA,
                logger=logging.Logger("nonce"),
            )

    def test_run_command(self) -> None:
        """
        The fake command is called when the command line specifies it
        """
        logger = logging.Logger("nonce")
        with mock.patch("sys.stdout", new=io.StringIO()) as fake_stdout, mock.patch(
            "sys.argv", new=["test", "fake"]
        ):
            entry.dunder_main(
                globals_dct=dict(__name__="__main__"),
                logger=logger,
                command_data=ENTRY_DATA,
            )
        assert_that(fake_stdout.getvalue(), contains_string("hello"))

    def test_with_prefix(self) -> None:
        """
        An explicit prefix overrides the default
        """
        ed = entry.EntryData.create("test_dunder_main", prefix="thing")
        assert_that(ed.prefix, equal_to("thing"))
