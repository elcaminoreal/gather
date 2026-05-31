"""Registration and dispatch to sub-commands."""

from __future__ import annotations
import argparse
import dataclasses
import os
import subprocess
import sys
from typing import Callable, Iterable, Mapping, Protocol, Sequence, TypeVar, cast

from commander_data.run import Runner

from .api import Collector, Wrapper, unique

_Element = TypeVar("_Element")


class ProcessRunner(Protocol):
    """Something that runs a subprocess, like ``subprocess.run``."""

    def __call__(self, *args: object, **kwargs: object) -> object:
        """Run a subprocess.

        Args:
            *args: positional arguments for the runner.
            **kwargs: keyword arguments for the runner.

        Returns:
            Whatever the underlying runner returns.
        """


def _default_run(*args: object, **kwargs: object) -> object:  # pragma: no cover
    return subprocess.run(*args, **kwargs)  # type: ignore[call-overload]


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class _Argument:
    args: Sequence[str]
    kwargs: frozenset[tuple[str, object]]


@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class CommandRegister:
    """A decorator factory that registers a command on a collector.

    Attributes:
        collector: the collector new commands are registered on.
    """

    collector: Collector  # noqa: SLD802

    def __call__(
        self, *args: object, name: str | None = None
    ) -> Callable[[_Element], _Element]:
        """Return a decorator that registers its argument.

        Args:
            *args: positional ``add_argument`` descriptions.
            name: optional name to register the command as.

        Returns:
            A decorator that registers and returns its argument unchanged.
        """
        return self.collector.register(transform=_transform(*args), name=name)


def add_argument(*args: str, **kwargs: object) -> _Argument:
    """Add an argument to a registered command.

    The arguments mirror ``argparse.ArgumentParser.add_argument``.

    Args:
        *args: positional arguments for ``add_argument``.
        **kwargs: keyword arguments for ``add_argument``.

    Returns:
        An opaque object describing the argument.
    """
    return _Argument(args=args, kwargs=frozenset(kwargs.items()))


def _transform(*args: object) -> Callable[[object], Wrapper]:
    return Wrapper.glue(args)


def make_command_register(collector: Collector) -> CommandRegister:  # noqa: SLD802
    """Return a decorator that registers a command.

    Args:
        collector: collector to add commands to.

    Returns:
        A callable that expects positional ``add_argument`` arguments and
        returns a decorator that registers the function to the collector.
    """
    return CommandRegister(collector=collector)


def _add_subparser(
    subparsers: "argparse._SubParsersAction[argparse.ArgumentParser]",  # noqa: SLD905
    name: str,
    wrapped: object,
) -> None:
    a_wrapper = cast(Wrapper, wrapped)  # noqa: SLD203
    arguments = cast("Sequence[_Argument]", a_wrapper.extra)  # noqa: SLD203
    a_subparser = subparsers.add_parser(name)
    a_subparser.set_defaults(
        __gather_name__=name,
        __gather_command__=a_wrapper.original,
    )
    for arg_details in arguments:
        a_subparser.add_argument(
            *arg_details.args,
            **dict(arg_details.kwargs),  # type: ignore[arg-type]
        )


def set_parser(
    *,
    collected: Mapping[str, Iterable[object]],
    parser: argparse.ArgumentParser | None = None,
) -> argparse.ArgumentParser:
    """Set (or create) a parser.

    The parser will dispatch to the functions collected, configuring the
    argument parsing according to each function's ``add_argument`` in the
    registration.

    Args:
        collected: return value from ``Collector.collect``.
        parser: an argument parser (one is created if not given).

    Returns:
        An argument parser.
    """
    if parser is None:
        parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    for name, wrapped in unique(collected).items():
        _add_subparser(subparsers, name, wrapped)
    return parser


def _normalize_argv(  # noqa: SLD609
    argv: Sequence[str],
    is_subcommand: bool,
    prefix: str | None,
) -> list[str]:
    argv_list = list(argv)
    if not is_subcommand:
        return argv_list
    argv_list[0:0] = [prefix or "base-command"]
    argv_list[1] = argv_list[1].rsplit("/", 1)[-1]
    if prefix is not None:
        argv_list[1] = argv_list[1].removeprefix(prefix + "-")
    return argv_list


def run_maybe_dry(  # noqa: SLD601,SLD602,SLD609
    *,
    parser: argparse.ArgumentParser,
    argv: Sequence[str] = sys.argv,
    env: Mapping[str, str] = os.environ,
    sp_run: ProcessRunner = _default_run,
    is_subcommand: bool = False,
    prefix: str | None = None,
) -> object:
    """Run commands that only take ``args``.

    Commands can assume that the following attributes exist: ``run`` (run
    with logging, only if ``--no-dry-run`` is passed), ``safe_run`` (run
    with logging) and ``orig_run`` (the original function).

    Args:
        parser: an argument parser.
        argv: ``sys.argv`` or something that looks like it.
        env: ``os.environ`` or something that looks like it.
        sp_run: ``subprocess.run`` or something that looks like it.
        is_subcommand: whether this is dispatched as a subcommand.
        prefix: optional subcommand prefix to strip.

    Returns:
        Return value from the dispatched command.
    """

    def error(*, args: argparse.Namespace) -> object:
        """Print help and exit when no command was selected.

        Args:
            args: the parsed arguments (unused).

        Returns:
            Never returns; raises ``SystemExit``.

        Raises:
            SystemExit: always, after printing help.
        """
        parser.print_help()
        raise SystemExit(1)

    namespace = parser.parse_args(_normalize_argv(argv, is_subcommand, prefix)[1:])
    namespace.orig_run = sp_run
    namespace.env = env
    a_runner = Runner.from_args(namespace)
    namespace.run, namespace.safe_run = a_runner.run, a_runner.safe_run
    command = getattr(namespace, "__gather_command__", error)
    return command(args=namespace)


def run(
    *,
    parser: argparse.ArgumentParser,
    argv: Sequence[str] = sys.argv,
    env: Mapping[str, str] = os.environ,
    sp_run: ProcessRunner = _default_run,
) -> object:
    """Parse arguments and run the command.

    Pass non-default arguments in testing scenarios.

    Args:
        parser: an argument parser.
        argv: ``sys.argv`` or something that looks like it.
        env: ``os.environ`` or something that looks like it.
        sp_run: ``subprocess.run`` or something that looks like it.

    Returns:
        Return value from the dispatched command.
    """
    namespace = parser.parse_args(list(argv)[1:])
    command = namespace.__gather_command__
    return command(args=namespace, env=env, run=sp_run)
