"""Test entrypoint"""
import io
import logging
import unittest
from unittest import mock

from hamcrest import assert_that, calling, contains_string, raises

from .. import entry

ENTRY_DATA = entry.EntryData.create("test_dunder_main")

@ENTRY_DATA.register()
def fake(args):
    print("hello")

class DunderMainTest(unittest.TestCase):

    """Test dunder_main"""

    def test_failed_import(self):
        assert_that(
            calling(entry.dunder_main).with_args(
                globals_dct=dict(__name__="some_name"),
                command_data=None,
                logger=None,
            ),
            raises(ImportError),
        )

    def test_run_command(self):
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
