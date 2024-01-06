"""Test entrypoint"""
import io
import logging
import unittest
from unittest import mock

from hamcrest import assert_that, calling, contains_string, equal_to, raises

from .. import entry

ENTRY_DATA = entry.EntryData.create("test_dunder_main")


@ENTRY_DATA.register(name="fake")
def _fake(args):
    print("hello")


class DunderMainTest(unittest.TestCase):

    """Test dunder_main"""

    def test_failed_import(self):
        """
        Function fails if the name is not __main__
        """
        assert_that(
            calling(entry.dunder_main).with_args(
                globals_dct=dict(__name__="some_name"),
                command_data=None,
                logger=None,
            ),
            raises(ImportError),
        )

    def test_run_command(self):
        """
        The fake command is called when the command line specifies it
        """
        logger = logging.Logger("nonce")
        mock_output = mock.patch("sys.stdout", new=io.StringIO())
        self.addCleanup(mock_output.stop)
        fake_stdout = mock_output.start()
        mock_args = mock.patch("sys.argv", new=[])
        self.addCleanup(mock_args.stop)
        fake_args = mock_args.start()
        fake_args[:] = ["test", "fake"]
        entry.dunder_main(
            globals_dct=dict(__name__="__main__"),
            logger=logger,
            command_data=ENTRY_DATA,
        )
        assert_that(fake_stdout.getvalue(), contains_string("hello"))

    def test_with_prefix(self):
        """
        An explicit prefix overrides the default
        """
        ed = entry.EntryData.create("test_dunder_main", prefix="thing")
        assert_that(ed.prefix, equal_to("thing"))
