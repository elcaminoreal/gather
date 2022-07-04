if __name__ != "__main__":
    raise ImportError("only run")

from . import main

collected = main.COMMANDS_COLLECTOR.collect()
print(collected)