from __future__ import annotations

import attrs

from .api import Wrapper, unique

@attrs.frozen
class Argument:
    args: Sequence[Any]
    kwargs: Sequence[Tuple[str, Any]]
    
def add_argument(*args, **kwargs):
    return Argument(args, frozenset(kwargs.items()))

def transform(*args):
    glue = Wrapper.glue(args)
    return glue
    
def make_command_register(collector):
    def register(*args, name=None):
        a_transform = transform(*args)
        return collector.register(transform=a_transform, name=name)
    return register

#def make_parser(collected):
#    commands = unique(collected)
#    for name, details in commands.items():
        
