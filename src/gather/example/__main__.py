"""Run the example commands"""

if __name__ != "__main__":
    raise ImportError("only run")

from . import main
from gather.commands import run

run(parser=main.get_parser())
