from __future__ import print_function

import gather

COMMANDS = gather.Collector()

BREAKFAST = gather.Collector()

@COMMANDS.register()
def hello(args):
    print("Hello", args)

@COMMANDS.register()
def goodbye(args):
    print("Goodbye", args)

@COMMANDS.register()
def breakfast(_args):
    foods = [klass() for klass in BREAKFAST.collect().values()]
    for food in foods:
        food.prepare()
    for food in foods:
        food.eat()

@BREAKFAST.register()
class Eggs(object):
    def prepare(self):
        print("Scrambling eggs")
    def eat(self):
        print("Devouring eggs")

@BREAKFAST.register()
class Cereal(object):
    def prepare(self):
        print("Mixing cereal and milk")
    def eat(self):
        print("Eating cereal with a spoon")

@BREAKFAST.register()
class OrangeJuice(object):
    def prepare(self):
        print("Squeezing orange juice")
    def eat(self):
        print("Drinking orange juice")
