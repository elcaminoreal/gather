import gather

WEIRD_COMMANDS = gather.Collector(depth=2)

def weird_decorator(func):
    WEIRD_COMMANDS.register()(func)
    return func
