"""Breakfast plugins"""
import logging

import gather

from . import ENTRY_DATA

BREAKFAST = gather.Collector()

LOGGER = logging.getLogger(__name__)


@ENTRY_DATA.register()
def breakfast(args):
    """Collect breakfast plugins, make breakfast"""
    foods = [klass() for klass in gather.unique(BREAKFAST.collect()).values()]
    for food in foods:
        food.prepare()
    for food in foods:
        food.eat()


@BREAKFAST.register()
class Eggs(object):

    """Eggs plugin for breakfast"""

    def prepare(self):
        """Prepare eggs by scrambling"""
        LOGGER.info("Scrambling eggs")

    def eat(self):
        """Eat the eggs by devouring"""
        LOGGER.info("Devouring eggs")


@BREAKFAST.register()
class Cereal(object):

    """Cereal plugin for breakfast"""

    def prepare(self):
        """Prepare cereal by mixing it with milk"""
        LOGGER.info("Mixing cereal and milk")

    def eat(self):
        """Eat cereal with a spoon"""
        LOGGER.info("Eating cereal with a spoon")


@BREAKFAST.register()
class OrangeJuice(object):

    """OJ plugin for breakfast"""

    def prepare(self):
        """Prepare juice by squeezing it"""
        LOGGER.info("Squeezing orange juice")

    def eat(self):
        """Consume the juice by drinking it"""
        LOGGER.info("Drinking orange juice")
