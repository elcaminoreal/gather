import sys

import gather

from gather.example import main

if __name__ != '__main__':
    raise ImportError("module cannot be imported")

gather.run(
    argv=sys.argv[1:],
    commands=main.COMMANDS.collect(),
    version=gather.__version__,
    output=sys.stdout,
)
