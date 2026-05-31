"""Breakfast plugins."""

import argparse
import dataclasses
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
    """Collect breakfast plugins and make breakfast.

    Args:
        args: the parsed command-line arguments (unused).
    """
    classes = cast(  # noqa: SLD203
        "Iterable[Callable[[], Food]]",
        unique(BREAKFAST.collect()).values(),
    )
    foods = [klass() for klass in classes]
    for item in foods:
        item.prepare()
    for item in foods:
        item.eat()


@BREAKFAST.register()
@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Eggs:
    """Eggs plugin for breakfast."""

    def prepare(self) -> None:  # noqa: SLD303
        """Prepare eggs by scrambling."""
        LOGGER.info("Scrambling eggs")

    def eat(self) -> None:  # noqa: SLD303
        """Eat the eggs by devouring."""
        LOGGER.info("Devouring eggs")


@BREAKFAST.register()
@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class Cereal:
    """Cereal plugin for breakfast."""

    def prepare(self) -> None:  # noqa: SLD303
        """Prepare cereal by mixing it with milk."""
        LOGGER.info("Mixing cereal and milk")

    def eat(self) -> None:  # noqa: SLD303
        """Eat cereal with a spoon."""
        LOGGER.info("Eating cereal with a spoon")


@BREAKFAST.register()
@dataclasses.dataclass(frozen=True, slots=True, kw_only=True)
class OrangeJuice:
    """OJ plugin for breakfast."""

    def prepare(self) -> None:  # noqa: SLD303
        """Prepare juice by squeezing it."""
        LOGGER.info("Squeezing orange juice")

    def eat(self) -> None:  # noqa: SLD303
        """Consume the juice by drinking it."""
        LOGGER.info("Drinking orange juice")
