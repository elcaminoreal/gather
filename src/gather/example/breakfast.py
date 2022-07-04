"""Breakfast plugins"""
import sys

import gather

BREAKFAST = gather.Collector()


def breakfast(_args):
    """Collect breakfast plugins, make breakfast"""
    foods = [klass() for klass in BREAKFAST.collect().values()]
    for food in foods:
        food.prepare()
    for food in foods:
        food.eat()


@BREAKFAST.register()
class Eggs(object):

    """Eggs plugin for breakfast"""

    def prepare(self):
        """Prepare eggs by scrambling"""
        sys.stdout.write("Scrambling eggs\n")

    def eat(self):
        """Eat the eggs by devouring"""
        sys.stdout.write("Devouring eggs\n")


@BREAKFAST.register()
class Cereal(object):

    """Cereal plugin for breakfast"""

    def prepare(self):
        """Prepare cereal by mixing it with milk"""
        sys.stdout.write("Mixing cereal and milk\n")

    def eat(self):
        """Eat cereal with a spoon"""
        sys.stdout.write("Eating cereal with a spoon\n")


@BREAKFAST.register()
class OrangeJuice(object):

    """OJ plugin for breakfast"""

    def prepare(self):
        """Prepare juice by squeezing it"""
        sys.stdout.write("Squeezing orange juice\n")

    def eat(self):
        """Consume the juice by drinking it"""
        sys.stdout.write("Drinking orange juice\n")
