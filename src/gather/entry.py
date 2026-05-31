"""Abstractions for writing entrypoints.

This is meant to reduce the overhead when writing a command with
subcommands.

In the example below,
the assumption is that your code is in the package
``awesomeawesome``.

In
``awesomeawesome/__init__.py``:

.. code::

    from gather import entry
    ENTRY_DATA = entry.EntryData.create(__name__)

In
``__main__.py``:

.. code::

    from gather import entry
    from . import ENTRY_DATA

    entry.dunder_main(
        globals_dct=globals(),
        command_data=ENTRY_DATA,
    )

Registering a new subcommand is done by adding the following to,
say,
``awesomeawesome/commands.py``:

.. code::

    from gather.commands import add_argument
    from . import ENTRY_DATA
    from commander_data import COMMAND


    @ENTRY_DATA.register()
    def hello(args):
        LOGGER.info("Hello world")


    @ENTRY_DATA.register(
        add_argument("--no-dry-run"),
        add_argument("--a-thing", default="the-thing"),
    )
    def frobnicate(args):
        args.run(
            COMMAND.rm(recursive=None, force=None)
        ) # Will only run with --no-dry-run
        hello = args.safe_run(
            COMMAND.echo("hello")
        ).stdout.strip() # Will run regardless

Note that commands can be added in any file,
as long as they are registered properly.

Optionally,
you can add script entry points
in
`pyproject.toml`:

.. code::

    [project.scripts]
    awesomeawesomectl = "awesomeawesome:ENTRY_DATA.main_command"
    frobnicate = "awesome:ENTRY_DATA.sub_command"

In that case,
the following will work:

* ``python -m awesomeawesome hello``
* ``awesomeawesome hello``
* ``python -m awesomeawesome frobnicate``
* ``awesomeawesome frobnicate``
* ``frobincate``

"""

from __future__ import annotations
import dataclasses
import functools
import logging
import runpy
import sys
from typing import Callable, Mapping

import toolz

from . import commands as commandslib, api


def dunder_main(
    globals_dct: Mapping[str, object],
    command_data: "EntryData",
    logger: logging.Logger = logging.getLogger(),
) -> None:
    """Call from ``__main__``.

    Args:
        globals_dct: the ``globals()`` of the calling ``__main__`` module.
        command_data: the entry data created for the package.
        logger: the logger to configure and use.

    Raises:
        ImportError: if ``globals_dct`` does not belong to ``__main__``.
    """
    if globals_dct["__name__"] != "__main__":
        raise ImportError("module cannot be imported", globals_dct["__name__"])
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    commandslib.run_maybe_dry(
        parser=commandslib.set_parser(collected=command_data.collector.collect()),
        is_subcommand=bool(globals_dct.get("IS_SUBCOMMAND", False)),
        prefix=command_data.prefix,
        argv=sys.argv,
    )


def _noop(_ignored: object) -> None:  # pragma: no cover
    pass


@dataclasses.dataclass(frozen=True)
class EntryData:
    """Data for the entry point.

    Attributes:
        prefix: the subcommand prefix.
        collector: the collector commands are registered on.
        register: the decorator factory used to register commands.
        main_command: callable that runs the package as ``__main__``.
        sub_command: callable that runs a single subcommand.
    """

    prefix: str
    collector: api.Collector  # noqa: SLD802
    register: commandslib.CommandRegister  # noqa: SLD802
    main_command: Callable[[], None]
    sub_command: Callable[[], None]

    @classmethod
    def create(  # noqa: SLD601
        cls, package_name: str, prefix: str | None = None
    ) -> "EntryData":
        """Create a new instance from a package name and prefix.

        Args:
            package_name: the importable name of the package.
            prefix: optional subcommand prefix (defaults to the package name).

        Returns:
            A new ``EntryData`` instance.
        """
        if prefix is None:
            prefix = package_name
        collector = api.Collector()
        register = commandslib.make_command_register(collector)
        main_command = toolz.compose(
            _noop,
            functools.partial(
                runpy.run_module,
                package_name,
                run_name="__main__",
            ),
        )
        sub_command = functools.partial(
            main_command, init_globals=dict(IS_SUBCOMMAND=True)
        )
        return cls(
            prefix=prefix,
            collector=collector,
            register=register,
            main_command=main_command,
            sub_command=sub_command,
        )
