"""Wrap a plugin registration in a function"""
import gather

WEIRD_COMMANDS = gather.Collector(depth=2)


def weird_decorator(func):
    """Register function into WEIRD_COMMANDS"""
    WEIRD_COMMANDS.register()(func)
    return func
