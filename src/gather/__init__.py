"""Gather: The Plugin Gatherer"""
import importlib.metadata

from gather.api import Collector, Wrapper, unique

__version__ = importlib.metadata.version(__name__)

__all__ = ["Collector", "Wrapper", "unique", "__version__"]
