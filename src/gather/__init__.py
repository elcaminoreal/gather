"""Gather: The Plugin Gatherer"""

from gather.api import Collector, run, Wrapper

__version__ = importlib.metadata.version(__name__)

__all__ = ['Collector', 'run', 'Wrapper', '__version__']
