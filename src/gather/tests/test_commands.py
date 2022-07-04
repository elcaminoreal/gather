"""Test command dispatch"""

import argparse
import io
import sys
import unittest
from unittest import mock
from hamcrest import (
    assert_that,
    string_contains_in_order,
    contains_string,
    calling,
    raises,
)


import gather
from gather import commands
from gather.commands import add_argument

COMMANDS_COLLECTOR = gather.Collector()

REGISTER = commands.make_command_register(COMMANDS_COLLECTOR)


@REGISTER(
    add_argument("--value", default="default-value"),
    name="do-something",
)
def _do_something(*, args, env, run):
    print(args.__gather_name__)
    print(args.value)
    print(env["SHELL"])
    run([sys.executable, "-c", "print(2)"], check=True)


@REGISTER(
    add_argument("--no-dry-run", action="store_true"),
    name="do-something-else",
)
def _do_something_else(*, args, env, run):
    print(args.no_dry_run)
    print(env["SHELL"])
    run([sys.executable, "-c", "print(3)"], check=True)


class CommandTest(unittest.TestCase):

    """Test command dispatch"""

    def setUp(self):
        """Set up sys.stdio and a mock process runner"""
        mock_output = mock.patch("sys.stdout", new=io.StringIO())
        self.addCleanup(mock_output.stop)
        self.fake_stdout = mock_output.start()

        def mini_python(argv, *args, check=False, **kwargs):
            if argv[:2] != [sys.executable, "-c"]:
                raise ValueError("only minipython", argv)
            details = argv[2].removeprefix("python(").removesuffix(")")
            print(details)

        self.fake_run = mock.MagicMock(side_effect=mini_python)

    def test_simple_command(self):
        """Running a command dispatches to the registered function"""
        parser = commands.set_parser(collected=COMMANDS_COLLECTOR.collect())
        commands.run(
            parser=parser,
            argv=["command", "do-something"],
            env=dict(SHELL="some-shell"),
            sp_run=self.fake_run,
        )
        output = self.fake_stdout.getvalue()
        assert_that(
            output,
            string_contains_in_order(
                "do-something",
                "default-value",
                "some-shell",
                "2",
            ),
        )

    def test_custom_parser(self):
        """Custom help message is printed out"""
        parser = commands.set_parser(
            collected=COMMANDS_COLLECTOR.collect(),
            parser=argparse.ArgumentParser(
                description="this is a custom help message",
            ),
        )
        assert_that(
            calling(commands.run).with_args(
                parser=parser,
                argv=["command", "--help"],
            ),
            raises(SystemExit),
        )
        output = self.fake_stdout.getvalue()
        assert_that(
            output,
            contains_string("custom help message"),
        )
