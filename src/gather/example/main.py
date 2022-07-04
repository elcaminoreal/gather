import sys
import gather
from gather import commands
from gather.commands import add_argument, transform

_COMMANDS_COLLECTOR = gather.Collector()
REGISTER = commands.make_command_register(_COMMANDS_COLLECTOR)


def get_parser():
    return commands.set_parser(collected=_COMMANDS_COLLECTOR.collect())


@REGISTER(
    add_argument("--value"),
    name="do-something",
)
def do_something(*, args, env, run):
    print(args.value)
    print(env["SHELL"])
    run([sys.executable, "-c", "print(1+1)"], check=True)


@REGISTER(
    add_argument("--no-dry-run", action="store_true"),
    name="do-something-else",
)
def do_something_else(*, args, env, run):
    print(args.no_dry_run)
    print(env["SHELL"])
    run([sys.executable, "-c", "print(1+1)"], check=True)
