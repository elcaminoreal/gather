"""Test command dispatch"""

import argparse
import contextlib
import io
import pathlib
import os
import tempfile
import textwrap
import subprocess
import sys
import unittest
from unittest import mock
from hamcrest import (
    assert_that,
    all_of,
    has_key,
    has_entry,
    not_,
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


MAYBE_DRY_COMMANDS_COLLECTOR = gather.Collector()

MAYBE_DRY_REGISTER = commands.make_command_register(MAYBE_DRY_COMMANDS_COLLECTOR)


@MAYBE_DRY_REGISTER(
    add_argument("--no-dry-run", action="store_true", default=False),
    add_argument("--output-dir", required=True),
    name="write-safely",
)
def _write_safely(args):
    output_dir = pathlib.Path(args.output_dir)
    safe = os.fspath(output_dir / "safe.txt")
    unsafe = os.fspath(output_dir / "unsafe.txt")
    code = textwrap.dedent(
        """\
    import pathlib
    import sys
    pathlib.Path(sys.argv[1]).write_text(str(1 + 1))
    """
    )
    args.run([sys.executable, "-c", code, unsafe])
    args.safe_run([sys.executable, "-c", code, safe])


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


class CommandMaybeDryTest(unittest.TestCase):

    """Test run_maybe_dry"""

    def test_error(self):
        """Help message is printed out"""
        parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
        mock_output = mock.patch("sys.stdout", new=io.StringIO())
        self.addCleanup(mock_output.stop)
        fake_stdout = mock_output.start()
        assert_that(
            calling(commands.run_maybe_dry).with_args(
                parser=parser,
                argv=["command"],
                env={},
                sp_run=subprocess.run,
            ),
            raises(SystemExit),
        )
        output = fake_stdout.getvalue()
        assert_that(
            output,
            contains_string("usage"),
        )

    def test_with_dry(self):
        """Test running command in dry-run mode"""
        parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
        with contextlib.ExitStack() as stack:
            tmp_dir = pathlib.Path(stack.enter_context(tempfile.TemporaryDirectory()))
            commands.run_maybe_dry(
                parser=parser,
                argv=["command", "write-safely", "--output-dir", os.fspath(tmp_dir)],
                env={},
                sp_run=subprocess.run,
            )
            contents = {child.name: child.read_text() for child in tmp_dir.iterdir()}
        assert_that(
            contents,
            all_of(
                not_(has_key("unsafe.txt")),
                has_entry("safe.txt", "2"),
            ),
        )

    def test_with_no_dry(self):
        """Test running command in no dry-run mode"""
        parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
        with contextlib.ExitStack() as stack:
            tmp_dir = pathlib.Path(stack.enter_context(tempfile.TemporaryDirectory()))
            commands.run_maybe_dry(
                parser=parser,
                argv=[
                    "command",
                    "write-safely",
                    "--output-dir",
                    os.fspath(tmp_dir),
                    "--no-dry-run",
                ],
                env={},
                sp_run=subprocess.run,
            )
            contents = {child.name: child.read_text() for child in tmp_dir.iterdir()}
        assert_that(
            contents,
            all_of(
                has_entry("unsafe.txt", "2"),
                has_entry("safe.txt", "2"),
            ),
        )

    def test_with_dry_fail(self):
        """Test running command that fails"""
        parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
        with contextlib.ExitStack() as stack:
            tmp_dir = pathlib.Path(stack.enter_context(tempfile.TemporaryDirectory()))
            assert_that(
                calling(commands.run_maybe_dry).with_args(
                    parser=parser,
                    argv=[
                        "command",
                        "write-safely",
                        "--output-dir",
                        os.fspath(tmp_dir / "not-there"),
                    ],
                    env={},
                    sp_run=subprocess.run,
                ),
                raises(subprocess.CalledProcessError),
            )

    def test_with_subcommand(self):
        """Test running command as subcommand"""
        parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
        with contextlib.ExitStack() as stack:
            tmp_dir = pathlib.Path(stack.enter_context(tempfile.TemporaryDirectory()))
            commands.run_maybe_dry(
                parser=parser,
                argv=[
                    "write-safely",
                    "--output-dir",
                    os.fspath(tmp_dir),
                    "--no-dry-run",
                ],
                is_subcommand=True,
                env={},
                sp_run=subprocess.run,
            )
            contents = {child.name: child.read_text() for child in tmp_dir.iterdir()}
        assert_that(
            contents,
            all_of(
                has_entry("unsafe.txt", "2"),
                has_entry("safe.txt", "2"),
            ),
        )

    def test_with_prefixed_subcommand(self):
        """Test running command as subcommand"""
        parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
        with contextlib.ExitStack() as stack:
            tmp_dir = pathlib.Path(stack.enter_context(tempfile.TemporaryDirectory()))
            commands.run_maybe_dry(
                parser=parser,
                argv=[
                    "command-write-safely",
                    "--output-dir",
                    os.fspath(tmp_dir),
                    "--no-dry-run",
                ],
                is_subcommand=True,
                prefix="command",
                env={},
                sp_run=subprocess.run,
            )
            contents = {child.name: child.read_text() for child in tmp_dir.iterdir()}
        assert_that(
            contents,
            all_of(
                has_entry("unsafe.txt", "2"),
                has_entry("safe.txt", "2"),
            ),
        )
