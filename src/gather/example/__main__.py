if __name__ != "__main__":
    raise ImportError("only run")

import gather
from . import main


collected = gather.unique(main.COMMANDS_COLLECTOR.collect())
print(collected)