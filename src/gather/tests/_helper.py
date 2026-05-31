"""Wrap a plugin registration in a function"""
from typing import TypeVar

import gather

_T = TypeVar("_T")

WEIRD_COMMANDS = gather.Collector(depth=2)


def weird_decorator(func: _T) -> _T:
    """Register function into WEIRD_COMMANDS"""
    WEIRD_COMMANDS.register()(func)
    return func
