from __future__ import print_function

import caparg

COMMANDS = caparg.Collector()

@COMMANDS.register()
def hello(args):
    print("Hello", args)

@COMMANDS.register()
def goodbye(args):
    print("Goodbye", args)
