# Register a plugin from a wrapper function, exercising a non-default depth.

from typing import TypeVar

import gather

_Element = TypeVar("_Element")

WEIRD_COMMANDS = gather.Collector(depth=2)


def weird_decorator(func: _Element) -> _Element:
    """Register a function into ``WEIRD_COMMANDS``.

    Args:
        func: the function to register.

    Returns:
        The argument, unchanged.
    """
    WEIRD_COMMANDS.register()(func)
    return func
