"""Test gather's API"""

import unittest

import six

import gather

from gather.tests import _helper

NICE_COMMANDS = gather.Collector()

EVIL_COMMANDS = gather.Collector()

@NICE_COMMANDS.register()
def main1(args):
    """Plugin registered with name of function"""
    return 'main1', args

@NICE_COMMANDS.register(name='weird_name')
def main2(args):
    """Plugin registered with explicit name"""
    return 'main2', args

@NICE_COMMANDS.register(name='bar')
@EVIL_COMMANDS.register(name='weird_name')
def main3(args):
    """Plugin registered for two collectors"""
    return 'main3', args

@EVIL_COMMANDS.register(name='baz')
def main4(args):
    """Plugin registered for the other collector"""
    return 'main4', args

@_helper.weird_decorator
def weird_function():
    """Plugin using a wrapper function to register"""
    pass

TRANSFORM_COMMANDS = gather.Collector()

@TRANSFORM_COMMANDS.register(transform=gather.Wrapper.glue(5))
def fooish():
    """Plugin registered with a transformation"""
    pass

COLLIDING_COMMANDS = gather.Collector()

NON_COLLIDING_COMMANDS = gather.Collector()

@NON_COLLIDING_COMMANDS.register(name='weird_name')
@COLLIDING_COMMANDS.register(name='weird_name')
def weird_name1():
    """One of several commands registered for same name"""
    pass

@COLLIDING_COMMANDS.register(name='weird_name')
def weird_name2():
    """One of several commands registered for same name"""
    pass

@COLLIDING_COMMANDS.register(name='weird_name')
def weird_name3():
    """One of several commands registered for same name"""
    pass

class CollectorTest(unittest.TestCase):

    """Tests for collecting plugins"""

    def test_collecting(self):
        """Collecting gives only the registered plugins for a given collector"""
        collected = NICE_COMMANDS.collect()
        self.assertIn('main1', collected)
        self.assertIs(collected['main1'], main1)
        self.assertNotIn('baz', collected)

    def test_non_collision(self):
        """Collecting with same name for different collectors does not collide"""
        nice = NICE_COMMANDS.collect()
        evil = EVIL_COMMANDS.collect()
        self.assertIs(nice['weird_name'], main2)
        self.assertIs(nice['bar'], main3)
        self.assertIs(evil['weird_name'], main3)

    def test_cross_module_collection(self):
        """Collection works when plugins are registered in a different module"""
        collected = _helper.WEIRD_COMMANDS.collect()
        self.assertIn('weird_function', collected)

    def test_transform(self):
        """Collecting transformed plugins applies transform on collection"""
        collected = TRANSFORM_COMMANDS.collect()
        self.assertIn('fooish', collected)
        res = collected.pop('fooish')
        self.assertIs(res.original, fooish)
        self.assertEquals(res.extra, 5)

    def test_one_of_strategy(self):
        """:code:`one_of` strategy returns one of the registered plugins

        The :code:`one_of` strategy returns one of the registered plugins
        for a given name.
        """
        collected = COLLIDING_COMMANDS.collect()
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertIn(weird_name, (weird_name1, weird_name2, weird_name3))

    def test_explicit_one_of_strategy(self):
        """:code:`one_of` strategy returns one of the registered plugins

        When asking explicitly for the :code:`one_of` strategy
        (as opposed to taking advantage of the default being that strategy)
        asking for a plugin by name gives one of the plugins registered
        to that name.
        """
        collected = COLLIDING_COMMANDS.collect(strategy=gather.Collector.one_of)
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertIn(weird_name, (weird_name1, weird_name2, weird_name3))

    def test_all_strategy(self):
        """:code:`all` strategy returns all the registered plugins for name"""
        collected = COLLIDING_COMMANDS.collect(strategy=gather.Collector.all)
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertEquals(weird_name, set([weird_name1, weird_name2, weird_name3]))

    def test_exactly_one_strategy(self):
        """:code:`exactly_one` strategy raises exception on collision

        A collision is when two plugins are registered to the same name"""
        with self.assertRaises(ValueError):
            COLLIDING_COMMANDS.collect(strategy=gather.Collector.exactly_one)
        collected = NON_COLLIDING_COMMANDS.collect(strategy=gather.Collector.exactly_one)
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertEquals(weird_name, weird_name1)


class RunTest(unittest.TestCase):

    """Test main runner"""

    def test_simple(self):
        """Subcommand calls the registered plugin for name of subcommand"""
        things = []
        commands = dict(simple=things.append)
        output = six.StringIO()
        gather.run(
            argv=['simple', 'world'],
            commands=commands,
            version='0.1.2',
            output=output,
        )
        self.assertEquals(things.pop(), ['simple', 'world'])

    def test_invalid(self):
        """Invalid Subcommand causes help to be printed"""
        things = []
        commands = dict(simple=things.append)
        output = six.StringIO()
        gather.run(
            argv=['lala'],
            commands=commands,
            version='0.1.2',
            output=output,
        )
        lines = output.getvalue().splitlines()
        self.assertEquals(lines.pop(0), 'Available subcommands:')
        self.assertEquals(lines.pop(0).strip(), 'simple')
        self.assertIn('--help', lines.pop(0))

    def test_empty(self):
        """Empty subcommand causes help to be printed"""
        things = []
        commands = dict(simple=things.append)
        output = six.StringIO()
        gather.run(
            argv=[],
            commands=commands,
            version='0.1.2',
            output=output,
        )
        lines = output.getvalue().splitlines()
        self.assertEquals(lines.pop(0), 'Available subcommands:')
        self.assertEquals(lines.pop(0).strip(), 'simple')
        self.assertIn('--help', lines.pop(0))

    def test_version(self):
        """Version subcommand causes version to be printed"""
        things = []
        commands = dict(simple=things.append)
        output = six.StringIO()
        gather.run(
            argv=['version'],
            commands=commands,
            version='0.1.2',
            output=output,
        )
        lines = output.getvalue().splitlines()
        self.assertEquals(lines.pop(0), 'Version 0.1.2')
