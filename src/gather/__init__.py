"""Gather: The Plugin Gatherer"""
import importlib.metadata

from gather.api import Collector, run, Wrapper

__version__ = importlib.metadata.version(__name__)

__all__ = ["Collector", "run", "Wrapper", "__version__"]
