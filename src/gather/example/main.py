import gather
from gather import commands
from gather.commands import add, transform

COMMANDS_COLLECTOR = gather.Collector()

@COMMANDS_COLLECTOR.register(transform=transform(
    add("--no-dry-run"),
))
def do_something(*, args, env, run):
    pass
