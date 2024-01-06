from __future__ import annotations
import functools
import logging
import runpy
import sys

import attrs
import toolz

from . import commands as commandslib, api

def dunder_main(globals_dct, command_data, logger=logging.getLogger()):
    if globals_dct["__name__"] != "__main__":
        raise ImportError("module cannot be imported", globals_dct["__name__"])
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(name)s:%(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    commandslib.run_maybe_dry(
        parser=commandslib.set_parser(collected=command_data.collector.collect()),
        is_subcommand=globals_dct.get("IS_SUBCOMMAND", False),
        prefix=command_data.prefix,
        argv=sys.argv,
    )
    
@attrs.frozen
class EntryData:
    prefix: str
    collector: api.Collector
    register: Callable
    main_command: Callable[[], None]
    sub_command: Callable[[], None]
    
    @classmethod
    def create(cls, package_name, prefix=None):
        if prefix is None:
            prefix = package_name
        collector = api.Collector()
        register = commandslib.make_command_register(collector)
        main_command = toolz.compose(
            lambda _ignored: None,
            functools.partial(
                runpy.run_module,
                package_name,
                run_name="__main__",
            ),
        )
        sub_command = functools.partial(main_command, init_globals=dict(IS_SUBCOMMAND=True))
        return cls(prefix=prefix, collector=collector, register=register, main_command=main_command, sub_command=sub_command)
