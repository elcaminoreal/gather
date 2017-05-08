import unittest

import six

import gather

from gather import _helper

NICE_COMMANDS = gather.Collector()

EVIL_COMMANDS = gather.Collector()

@NICE_COMMANDS.register()
def main1(args):
    return 'main1', args

@NICE_COMMANDS.register(name='weird_name')
def main2(args):
    return 'main2', args

@NICE_COMMANDS.register(name='bar')
@EVIL_COMMANDS.register(name='weird_name')
def main3(args):
    return 'main3', args

@EVIL_COMMANDS.register(name='baz')
def main4(args):
    return 'main4', args

@_helper.weird_decorator
def weird_function():
    pass

TRANSFORM_COMMANDS = gather.Collector()

@TRANSFORM_COMMANDS.register(transform=gather.Wrapper.glue(5))
def fooish():
    pass

CONFLICTING_COMMANDS = gather.Collector()

NON_CONFLICTING_COMMANDS = gather.Collector()

@NON_CONFLICTING_COMMANDS.register(name='weird_name')
@CONFLICTING_COMMANDS.register(name='weird_name')
def weird_name1():
    pass

@CONFLICTING_COMMANDS.register(name='weird_name')
def weird_name2():
    pass

@CONFLICTING_COMMANDS.register(name='weird_name')
def weird_name3():
    pass

class CollectorTest(unittest.TestCase):

    def test_collecting(self):
        collected = NICE_COMMANDS.collect()
        self.assertIn('main1', collected)
        self.assertIs(collected['main1'], main1)
        self.assertNotIn('baz', collected)

    def test_non_collision(self):
        nice = NICE_COMMANDS.collect()
        evil = EVIL_COMMANDS.collect()
        self.assertIs(nice['weird_name'], main2)
        self.assertIs(nice['bar'], main3)
        self.assertIs(evil['weird_name'], main3)

    def test_cross_module_collection(self):
        collected = _helper.WEIRD_COMMANDS.collect()
        self.assertIn('weird_function', collected)

    def test_transform(self):
        collected = TRANSFORM_COMMANDS.collect()
        self.assertIn('fooish', collected)
        res = collected.pop('fooish')
        self.assertIs(res.original, fooish)
        self.assertEquals(res.extra, 5)

    def test_one_of_strategy(self):
        collected = CONFLICTING_COMMANDS.collect()
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertIn(weird_name, (weird_name1, weird_name2, weird_name3))

    def test_explicit_one_of_strategy(self):
        collected = CONFLICTING_COMMANDS.collect(strategy=gather.Collector.one_of)
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertIn(weird_name, (weird_name1, weird_name2, weird_name3))

    def test_all_strategy(self):
        collected = CONFLICTING_COMMANDS.collect(strategy=gather.Collector.all)
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertEquals(weird_name, set([weird_name1, weird_name2, weird_name3]))

    def test_conflicting_strategy(self):
        with self.assertRaises(ValueError):
            CONFLICTING_COMMANDS.collect(strategy=gather.Collector.conflict)
        collected = NON_CONFLICTING_COMMANDS.collect(strategy=gather.Collector.conflict)
        weird_name = collected.pop('weird_name')
        self.assertEquals(collected, {})
        self.assertEquals(weird_name, weird_name1)

class RunTest(unittest.TestCase):

    def test_simple(self):
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
