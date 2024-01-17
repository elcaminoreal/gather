"""Registration and dispatch to sub-commands"""

from __future__ import annotations
import argparse
import logging
import os
import sys
import subprocess
from typing import Sequence, Any, Tuple

import attrs
from commander_data.run import Runner

from .api import Wrapper, unique

LOGGER = logging.getLogger(__name__)


@attrs.frozen
class _Argument:
    args: Sequence[Any]
    kwargs: Sequence[Tuple[str, Any]]


def add_argument(*args, **kwargs):
    """
    Add argument to a registered command.

    See :code:`argparse.ArgumentParser.add_argument`
    for a description of the argument semantics.
    """
    return _Argument(args, frozenset(kwargs.items()))


def _transform(*args):
    glue = Wrapper.glue(args)
    return glue


def make_command_register(collector):
    """
    Return a decorator that registers a command.

    Args:
        collector: Collector to add commands to

    Returns:
        Callable that expects positional add_argument arguments,
        and returns a decorator that registers the function
        to the collector.
    """

    def _register(*args, name=None):
        a_transform = _transform(*args)
        return collector.register(transform=a_transform, name=name)

    return _register


def set_parser(*, collected, parser=None):
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
        original = details.original
        args = details.extra
        a_subparser = subparsers.add_parser(name)
        a_subparser.set_defaults(
            __gather_name__=name,
            __gather_command__=original,
        )
        for arg_details in args:
            a_subparser.add_argument(*arg_details.args, **dict(arg_details.kwargs))
    return parser


def run_maybe_dry(
    *,
    parser,
    argv=sys.argv,
    env=os.environ,
    sp_run=subprocess.run,
    is_subcommand=False,
    prefix=None,
):
    """
    Run commands that only take ``args``.

    This runs commands that take ``args``.
    Commands can assume that the following attributes
    exist:

    * ``run``: Run with logging, only if `--no-dry-run` is passed
    * ``safe_run``: Run with logging
    * ``orig_run``: Original function
    """

    def error(args):
        parser.print_help()
        raise SystemExit(1)

    argv = list(argv)
    if is_subcommand:
        argv[0:0] = [prefix or "base-command"]
        argv[1] = argv[1].rsplit("/", 1)[-1]
        if prefix is not None:
            argv[1] = argv[1].removeprefix(prefix + "-")

    args = parser.parse_args(argv[1:])
    args.orig_run = sp_run
    a_runner = Runner.from_args(args)
    args.run = a_runner.run
    args.safe_run = a_runner.safe_run
    args.env = env
    getattr(args, "__gather_command__", error)(args)


def run(*, parser, argv=sys.argv, env=os.environ, sp_run=subprocess.run):
    """
    Parse arguments and run the command.

    Pass non-default args in testing scenarios.

    Args:
        argv: sys.argv or something that looks like it
        env: os.environ or something that looks like it
        sp_run: subprocess.run or something that looks like it

    Returns:
        Return value from dispatched command
    """
    args = parser.parse_args(argv[1:])
    command = args.__gather_command__
    return command(
        args=args,
        env=env,
        run=sp_run,
    )
