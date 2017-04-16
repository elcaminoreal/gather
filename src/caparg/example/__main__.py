import sys

import caparg

from caparg.example import main

if __name__ != '__main__':
    raise ImportError("module cannot be imported")

caparg.run(
    argv=sys.argv[1:],
    commands=main.COMMANDS.collect(),
    version=caparg.__version__,
    output=sys.stdout,
)
