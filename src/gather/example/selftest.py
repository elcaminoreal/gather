"""Self-test entry point"""
from __future__ import print_function

import ast
import subprocess
import sys

from gather.example import main as cemain


@cemain.COMMANDS.register()
def selftest(_args):
    """
    Use example plugins to run a self-test

    This subcommand runs other subcommands that are registered,
    to see that registration in general works correctly.
    """
    command_prefix = [sys.executable, "-m", "gather.example"]
    hello = command_prefix + ["hello", "world"]
    res = subprocess.check_output(hello).decode("utf-8")
    greeting, contents = res.split(None, 1)
    if greeting != "Hello":
        raise ValueError("Incorrect greeting", res)
    parsed = ast.literal_eval(contents)
    if parsed != ["hello", "world"]:
        raise ValueError("Incorrect arguments", res)
