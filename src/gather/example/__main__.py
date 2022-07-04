if __name__ != "__main__":
    raise ImportError("only run")

from gather import commands
from . import main

parser = commands.set_parser(collected=main.COMMANDS_COLLECTOR.collect())
parser.parse_args()
