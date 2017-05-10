"""Commands for self-test/example"""

from __future__ import print_function

import gather

COMMANDS = gather.Collector()

BREAKFAST = gather.Collector()

@COMMANDS.register()
def hello(args):
    """Say hello, print arguments"""
    print("Hello", args)

@COMMANDS.register()
def goodbye(args):
    """Say goodbye, print arguments"""
    print("Goodbye", args)

@COMMANDS.register()
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
        print("Scrambling eggs")
    def eat(self):
        """Eat the eggs by devouring"""
        print("Devouring eggs")

@BREAKFAST.register()
class Cereal(object):
    """Cereal plugin for breakfast"""
    def prepare(self):
        """Prepare cereal by mixing it with milk"""
        print("Mixing cereal and milk")
    def eat(self):
        """Eat cereal with a spoon"""
        print("Eating cereal with a spoon")

@BREAKFAST.register()
class OrangeJuice(object):
    """OJ plugin for breakfast"""
    def prepare(self):
        """Prepare juice by squeezing it"""
        print("Squeezing orange juice")
    def eat(self):
        """Consume the juice by drinking it"""
        print("Drinking orange juice")
