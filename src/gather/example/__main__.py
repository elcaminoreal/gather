if __name__ != "__main__":
    raise ImportError("only run")

import os
import subprocess
import sys
from gather import commands
from . import main

commands.run(
    parser=commands.set_parser(collected=main.COMMANDS_COLLECTOR.collect()),
    env=os.environ,
    argv=sys.argv,
    sp_run=subprocess.run,
)
