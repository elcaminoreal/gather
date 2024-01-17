"""Run the example commands"""
from gather import entry
from . import ENTRY_DATA

entry.dunder_main(
    globals_dct=globals(),
    command_data=ENTRY_DATA,
)
