"""Breakfast plugins"""

import argparse
import logging
from typing import Callable, Iterable, Protocol, cast

from gather import Collector, unique

from . import ENTRY_DATA

BREAKFAST = Collector()

LOGGER = logging.getLogger(__name__)


class Food(Protocol):
    """Something that can be prepared and eaten."""

    def prepare(self) -> None:
        """Prepare the food."""

    def eat(self) -> None:
        """Eat the food."""


@ENTRY_DATA.register()
def breakfast(args: argparse.Namespace) -> None:
    """Collect breakfast plugins, make breakfast"""
    classes = cast(
        "Iterable[Callable[[], Food]]",
        unique(BREAKFAST.collect()).values(),
    )
    foods = [klass() for klass in classes]
    for food in foods:
        food.prepare()
    for food in foods:
        food.eat()


@BREAKFAST.register()
class Eggs:
    """Eggs plugin for breakfast"""

    def prepare(self) -> None:
        """Prepare eggs by scrambling"""
        LOGGER.info("Scrambling eggs")

    def eat(self) -> None:
        """Eat the eggs by devouring"""
        LOGGER.info("Devouring eggs")


@BREAKFAST.register()
class Cereal:
    """Cereal plugin for breakfast"""

    def prepare(self) -> None:
        """Prepare cereal by mixing it with milk"""
        LOGGER.info("Mixing cereal and milk")

    def eat(self) -> None:
        """Eat cereal with a spoon"""
        LOGGER.info("Eating cereal with a spoon")


@BREAKFAST.register()
class OrangeJuice:
    """OJ plugin for breakfast"""

    def prepare(self) -> None:
        """Prepare juice by squeezing it"""
        LOGGER.info("Squeezing orange juice")

    def eat(self) -> None:
        """Consume the juice by drinking it"""
        LOGGER.info("Drinking orange juice")
