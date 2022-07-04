from __future__ import annotations

import attrs

from .api import Wrapper

@attrs.frozen
class Argument:
    args: Sequence[Any]
    kwargs: Sequence[Tuple[str, Any]]
    
def add(*args, **kwargs):
    return Argument(args, frozenset(kwargs.items()))

@attrs.frozen
class Command:
    name: str
    args: Sequence[Argument]

def transform(*args, name=None):
    command = Command(name, args)
    glue = Wrapper.glue(command)
    return glue
    
def make_command_register(collector):
    def register(*args, name=None):
        return collector.register(transform=glue)
    return register
