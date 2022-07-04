"""Test gather's API"""
import unittest

import gather
from gather import unique

from gather.tests import _helper

MAIN_COMMANDS = gather.Collector()

OTHER_COMMANDS = gather.Collector()


@MAIN_COMMANDS.register()
def main1(args):
    """Plugin registered with name of function"""
    return "main1", args


@MAIN_COMMANDS.register(name="weird_name")
def main2(args):
    """Plugin registered with explicit name"""
    return "main2", args


@MAIN_COMMANDS.register(name="bar")
@OTHER_COMMANDS.register(name="weird_name")
def main3(args):
    """Plugin registered for two collectors"""
    return "main3", args


@OTHER_COMMANDS.register(name="baz")
def main4(args):
    """Plugin registered for the other collector"""
    return "main4", args


@_helper.weird_decorator
def weird_function():
    """Plugin using a wrapper function to register"""


TRANSFORM_COMMANDS = gather.Collector()


@TRANSFORM_COMMANDS.register(transform=gather.Wrapper.glue(5))
def fooish():
    """Plugin registered with a transformation"""


COLLIDING_COMMANDS = gather.Collector()

NON_COLLIDING_COMMANDS = gather.Collector()


@NON_COLLIDING_COMMANDS.register(name="weird_name")
@COLLIDING_COMMANDS.register(name="weird_name")
def weird_name1():
    """One of several commands registered for same name"""


@COLLIDING_COMMANDS.register(name="weird_name")
def weird_name2():
    """One of several commands registered for same name"""


@COLLIDING_COMMANDS.register(name="weird_name")
def weird_name3():
    """One of several commands registered for same name"""


class CollectorTest(unittest.TestCase):

    """Tests for collecting plugins"""

    def test_collecting(self):
        """Collecting gives only the registered plugins for a given collector"""
        collected = unique(MAIN_COMMANDS.collect())
        self.assertIn("main1", collected)
        self.assertIs(collected["main1"], main1)
        self.assertNotIn("baz", collected)

    def test_non_collision(self):
        """Collecting with same name for different collectors does not collide"""
        main = unique(MAIN_COMMANDS.collect())
        other = unique(OTHER_COMMANDS.collect())
        self.assertIs(main["weird_name"], main2)
        self.assertIs(main["bar"], main3)
        self.assertIs(other["weird_name"], main3)

    def test_cross_module_collection(self):
        """Collection works when plugins are registered in a different module"""
        collected = unique(_helper.WEIRD_COMMANDS.collect())
        self.assertIn("weird_function", collected)

    def test_transform(self):
        """Collecting transformed plugins applies transform on collection"""
        collected = unique(TRANSFORM_COMMANDS.collect())
        self.assertIn("fooish", collected)
        res = collected.pop("fooish")
        self.assertIs(res.original, fooish)
        self.assertEqual(res.extra, 5)

    def test_multiple(self):
        """Without unique, it gets all the registered plugins for name"""
        collected = COLLIDING_COMMANDS.collect()
        weird_name = collected.pop("weird_name")
        self.assertEqual(collected, {})
        self.assertEqual(weird_name, set([weird_name1, weird_name2, weird_name3]))

    def test_multiple_unique_fails(self):
        """Without unique, it gets all the registered plugins for name"""
        with self.assertRaises(ValueError):
            unique(COLLIDING_COMMANDS.collect())
