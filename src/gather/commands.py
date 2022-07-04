from __future__ import annotations
import argparse

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

def set_parser(*, collected, parser=None):
    if parser is None:
        parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    commands = unique(collected)
    for name, details in commands.items():
        original = details.original
        args = details.extra
        a_subparser = subparsers.add_parser(name)
        a_subparser.set_defaults(
            __gather_name__=name,
            __gather_command__=original,
        )
        for arg_details in args:
            a_subparser.add_argument(*arg_details.args, **dict(arg_details.kwargs))
    return parser

def run(*, parser, argv, env, sp_run):
    args = parser.parse_args(argv[1:])
    command = args.__gather_command__
    return command(
        args=args,
        env=env,
        run=sp_run,
    )
