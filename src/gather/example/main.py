import gather
from gather import commands
from gather.commands import add_argument, transform

COMMANDS_COLLECTOR = gather.Collector()

REGISTER = commands.make_command_register(COMMANDS_COLLECTOR)

@REGISTER(
    add_argument("--no-dry-run"),
)
def do_something(*, args, env, run):
    pass

@REGISTER(
    add_argument("--no-dry-run"),
)
def do_something_else(*, args, env, run):
    pass
