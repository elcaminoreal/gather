"""Test command dispatch."""

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
from typing import Mapping, Sequence
from unittest import mock
from hamcrest import (
    assert_that,
    string_contains_in_order,
    contains_string,
)


import gather
from gather import commands
from gather.commands import ProcessRunner, add_argument


# Conforming ProcessRunner wrapper around subprocess.run.
def _run(*args: object, **kwargs: object) -> object:
    return subprocess.run(*args, **kwargs)  # type: ignore[call-overload]


COMMANDS_COLLECTOR = gather.Collector()

REGISTER = commands.make_command_register(COMMANDS_COLLECTOR)


@REGISTER(
    add_argument("--value", default="default-value"),
    name="do-something",
)
def _do_something(
    *, args: argparse.Namespace, env: Mapping[str, str], run: ProcessRunner
) -> None:
    print(args.__gather_name__)
    print(args.value)
    print(env["SHELL"])
    run([sys.executable, "-c", "print(2)"], check=True)


@REGISTER(
    add_argument("--no-dry-run", action="store_true"),
    name="do-something-else",
)
def _do_something_else(
    *, args: argparse.Namespace, env: Mapping[str, str], run: ProcessRunner
) -> None:
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
def _write_safely(args: argparse.Namespace) -> None:
    output_dir = pathlib.Path(args.output_dir)
    safe = os.fspath(output_dir / "safe.txt")
    unsafe = os.fspath(output_dir / "unsafe.txt")
    code = textwrap.dedent("""\
    import pathlib
    import sys
    pathlib.Path(sys.argv[1]).write_text(str(1 + 1))
    """)
    args.run([sys.executable, "-c", code, unsafe])
    args.safe_run([sys.executable, "-c", code, safe])


def _make_fake_run() -> mock.MagicMock:
    """Build a fake process runner that echoes a minimal python ``-c`` body.

    Returns:
        A ``MagicMock`` whose side effect prints the executed snippet.
    """

    def mini_python(
        argv: Sequence[str],
        *positional: object,
        check: bool = False,
        **kwargs: object,
    ) -> None:
        if argv[:2] != [sys.executable, "-c"]:
            raise ValueError("only minipython", argv)
        details = argv[2].removeprefix("python(").removesuffix(")")
        print(details)

    return mock.MagicMock(side_effect=mini_python)


def _read_dir(directory: pathlib.Path) -> Mapping[str, str]:
    """Read every file in a directory into a name-to-text mapping.

    Args:
        directory: the directory to read.

    Returns:
        A mapping of file name to file contents.
    """
    return {child.name: child.read_text() for child in directory.iterdir()}


def _dispatch_write_safely(
    *,
    leading: Sequence[str],
    no_dry_run: bool,
    is_subcommand: bool = False,
    prefix: str | None = None,
    output_subdir: str | None = None,
) -> Mapping[str, str]:
    """Run the ``write-safely`` command against a fresh temp directory.

    Args:
        leading: argv tokens that precede ``--output-dir``.
        no_dry_run: whether to append ``--no-dry-run``.
        is_subcommand: whether to dispatch as a subcommand.
        prefix: optional subcommand prefix.
        output_subdir: optional missing subdirectory to target (for the
            failure case).

    Returns:
        The contents of the temp directory after the command runs.
    """
    parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
    with tempfile.TemporaryDirectory() as raw:
        tmp_dir = pathlib.Path(raw)
        target = tmp_dir if output_subdir is None else tmp_dir / output_subdir
        argv = [*leading, "--output-dir", os.fspath(target)]
        if no_dry_run:
            argv.append("--no-dry-run")
        commands.run_maybe_dry(
            parser=parser,
            argv=argv,
            env={},
            sp_run=_run,
            is_subcommand=is_subcommand,
            prefix=prefix,
        )
        return _read_dir(tmp_dir)


class CommandTest(unittest.TestCase):
    """Test command dispatch."""

    def test_simple_command(self) -> None:
        """Running a command dispatches to the registered function."""
        parser = commands.set_parser(collected=COMMANDS_COLLECTOR.collect())
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            commands.run(
                parser=parser,
                argv=["command", "do-something"],
                env=dict(SHELL="some-shell"),
                sp_run=_make_fake_run(),
            )
        assert_that(
            stream.getvalue(),
            string_contains_in_order(
                "do-something",
                "default-value",
                "some-shell",
                "2",
            ),
        )

    def test_custom_parser(self) -> None:
        """Custom help message is printed out."""
        parser = commands.set_parser(
            collected=COMMANDS_COLLECTOR.collect(),
            parser=argparse.ArgumentParser(
                description="this is a custom help message",
            ),
        )
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), self.assertRaises(SystemExit):
            commands.run(
                parser=parser,
                argv=["command", "--help"],
            )
        assert_that(stream.getvalue(), contains_string("custom help message"))


class CommandMaybeDryTest(unittest.TestCase):
    """Test run_maybe_dry."""

    def test_error(self) -> None:
        """Help message is printed out."""
        parser = commands.set_parser(collected=MAYBE_DRY_COMMANDS_COLLECTOR.collect())
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), self.assertRaises(SystemExit):
            commands.run_maybe_dry(
                parser=parser,
                argv=["command"],
                env={},
                sp_run=_run,
            )
        assert_that(stream.getvalue(), contains_string("usage"))

    def test_with_dry(self) -> None:
        """A dry run writes only the safe file."""
        contents = _dispatch_write_safely(
            leading=["command", "write-safely"], no_dry_run=False
        )
        self.assertNotIn("unsafe.txt", contents)
        self.assertEqual(contents["safe.txt"], "2")

    def test_with_no_dry(self) -> None:
        """A no-dry run writes both files."""
        contents = _dispatch_write_safely(
            leading=["command", "write-safely"], no_dry_run=True
        )
        self.assertEqual(contents["unsafe.txt"], "2")
        self.assertEqual(contents["safe.txt"], "2")

    def test_with_dry_fail(self) -> None:
        """A command targeting a missing directory raises."""
        with self.assertRaises(subprocess.CalledProcessError):
            _dispatch_write_safely(
                leading=["command", "write-safely"],
                no_dry_run=False,
                output_subdir="not-there",
            )

    def test_with_subcommand(self) -> None:
        """Dispatch works when invoked as a subcommand."""
        contents = _dispatch_write_safely(
            leading=["write-safely"], no_dry_run=True, is_subcommand=True
        )
        self.assertEqual(contents["unsafe.txt"], "2")
        self.assertEqual(contents["safe.txt"], "2")

    def test_with_prefixed_subcommand(self) -> None:
        """Dispatch works for a prefixed subcommand."""
        contents = _dispatch_write_safely(
            leading=["command-write-safely"],
            no_dry_run=True,
            is_subcommand=True,
            prefix="command",
        )
        self.assertEqual(contents["unsafe.txt"], "2")
        self.assertEqual(contents["safe.txt"], "2")
