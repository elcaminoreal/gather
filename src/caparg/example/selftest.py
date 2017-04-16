from __future__ import print_function

from caparg.example import main as cemain

@cemain.COMMANDS.register()
def selftest(args):
    raise SystemExit("not working")
