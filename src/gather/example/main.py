"""Example commands"""
import sys

from commander_data.common import LOCAL_PYTHON as PYTHON

import gather
from gather import commands
from gather.commands import add_argument

from . import ENTRY_DATA

def get_parser():
    """Get parser dispatching to example commands"""
    return commands.set_parser(collected=_COMMANDS_COLLECTOR.collect())


@ENTRY_DATA.register(
    add_argument("--value"),
    name="do-something",
)
def _do_something(args):
    print(args.value)
    print(args.env["SHELL"])
    args.safe_run(PYTHON(c="print(1+1)"), capture_output=False)


@ENTRY_DATA.register(
    add_argument("--no-dry-run", action="store_true"),
    name="do-something-else",
)
def _do_something_else(args):
    print(args.no_dry_run)
    print(args.env["SHELL"])
    args.safe_run(PYTHON(c="print(1+1)"), capture_output=False)
