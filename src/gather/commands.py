"""Registration and dispatch to sub-commands"""

from __future__ import annotations
import argparse
import os
import subprocess
import sys
from typing import Callable, Iterable, Mapping, Protocol, Sequence, TypeVar, cast

import attrs
from commander_data.run import Runner

from .api import Collector, Wrapper, unique

_F = TypeVar("_F")


class ProcessRunner(Protocol):
    """Something that runs a subprocess, like :code:`subprocess.run`."""

    def __call__(self, *args: object, **kwargs: object) -> object:
        """Run a subprocess.

        Args:
            args: positional arguments for the runner
            kwargs: keyword arguments for the runner

        Returns:
            Whatever the underlying runner returns.
        """


@attrs.frozen
class _Argument:
    args: Sequence[str]
    kwargs: frozenset[tuple[str, object]]


@attrs.frozen
class CommandRegister:
    """A decorator factory that registers a command on a collector."""

    collector: Collector

    def __call__(self, *args: object, name: str | None = None) -> Callable[[_F], _F]:
        """Return a decorator that registers its argument.

        Args:
            args: positional :func:`add_argument` descriptions
            name: optional name to register the command as

        Returns:
            A decorator that registers and returns its argument unchanged.
        """
        a_transform = _transform(*args)
        return self.collector.register(transform=a_transform, name=name)


def add_argument(*args: str, **kwargs: object) -> _Argument:
    """
    Add argument to a registered command.

    See :code:`argparse.ArgumentParser.add_argument`
    for a description of the argument semantics.

    Args:
        args: positional arguments for :code:`add_argument`
        kwargs: keyword arguments for :code:`add_argument`

    Returns:
        An opaque object describing the argument.
    """
    return _Argument(args, frozenset(kwargs.items()))


def _transform(*args: object) -> Callable[[object], Wrapper]:
    glue = Wrapper.glue(args)
    return glue


def make_command_register(collector: Collector) -> CommandRegister:
    """
    Return a decorator that registers a command.

    Args:
        collector: Collector to add commands to

    Returns:
        Callable that expects positional add_argument arguments,
        and returns a decorator that registers the function
        to the collector.
    """
    return CommandRegister(collector)


def set_parser(
    *,
    collected: Mapping[str, Iterable[object]],
    parser: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    """
    Set (or create) a parser.

    The parser will dispatch to the functions collected.
    The parser will configure the argument parsing according to the
    function's :code:`add_argument` in the registration.

    Args:
        collected: Return value from :code:`Collector.collected`
        parser: an argument parser

    Returns:
        An argument parser
    """
    if parser is None:
        parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    commands = unique(collected)
    for name, details in commands.items():
        a_wrapper = cast(Wrapper, details)
        original = a_wrapper.original
        args = cast("Sequence[_Argument]", a_wrapper.extra)
        a_subparser = subparsers.add_parser(name)
        a_subparser.set_defaults(
            __gather_name__=name,
            __gather_command__=original,
        )
        for arg_details in args:
            a_subparser.add_argument(
                *arg_details.args,
                **dict(arg_details.kwargs),  # type: ignore[arg-type]
            )
    return parser


def run_maybe_dry(
    *,
    parser: argparse.ArgumentParser,
    argv: Sequence[str] = sys.argv,
    env: Mapping[str, str] = os.environ,
    sp_run: ProcessRunner = subprocess.run,
    is_subcommand: bool = False,
    prefix: str | None = None,
) -> object:
    """
    Run commands that only take ``args``.

    This runs commands that take ``args``.
    Commands can assume that the following attributes
    exist:

    * ``run``: Run with logging, only if `--no-dry-run` is passed
    * ``safe_run``: Run with logging
    * ``orig_run``: Original function

    Args:
        parser: an argument parser
        argv: sys.argv or something that looks like it
        env: os.environ or something that looks like it
        sp_run: subprocess.run or something that looks like it
        is_subcommand: whether this is dispatched as a subcommand
        prefix: optional subcommand prefix to strip

    Returns:
        Return value from dispatched command
    """

    def error(args: argparse.Namespace) -> object:
        parser.print_help()
        raise SystemExit(1)

    argv_list = list(argv)
    if is_subcommand:
        argv_list[0:0] = [prefix or "base-command"]
        argv_list[1] = argv_list[1].rsplit("/", 1)[-1]
        if prefix is not None:
            argv_list[1] = argv_list[1].removeprefix(prefix + "-")

    args = parser.parse_args(argv_list[1:])
    args.orig_run = sp_run
    args.env = env
    a_runner = Runner.from_args(args)
    args.run, args.safe_run = a_runner.run, a_runner.safe_run
    try:
        command = args.__gather_command__
    except AttributeError:
        command = error
    return command(
        args=args,
    )


def run(
    *,
    parser: argparse.ArgumentParser,
    argv: Sequence[str] = sys.argv,
    env: Mapping[str, str] = os.environ,
    sp_run: ProcessRunner = subprocess.run,
) -> object:
    """
    Parse arguments and run the command.

    Pass non-default args in testing scenarios.

    Args:
        parser: an argument parser
        argv: sys.argv or something that looks like it
        env: os.environ or something that looks like it
        sp_run: subprocess.run or something that looks like it

    Returns:
        Return value from dispatched command
    """
    args = parser.parse_args(list(argv)[1:])
    command = args.__gather_command__
    return command(
        args=args,
        env=env,
        run=sp_run,
    )
