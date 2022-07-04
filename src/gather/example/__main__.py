if __name__ != "__main__":
    raise ImportError("only run")

from gather import commands
from . import main


collected = main.COMMANDS_COLLECTOR.collect()
print(collected)
parser = commands.set_parser(collected)
