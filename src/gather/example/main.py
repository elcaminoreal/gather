import gather
from gather import commands
from gather.commands import add_argument, transform

COMMANDS_COLLECTOR = gather.Collector()

REGISTER = commands.make_command_register(COMMANDS_COLLECTOR)

@REGISTER(
    add_argument("--value"),
    name="do-something",
)
def do_something(*, args, env, run):
    pass

@REGISTER(
    add_argument("--no-dry-run", action="store_true"),
    name="do-something-else",
)
def do_something_else(*, args, env, run):
    pass
