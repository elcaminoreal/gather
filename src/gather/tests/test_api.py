"""Test gather's API."""

import unittest
from typing import cast

import gather
from gather import Wrapper, unique

from . import _weird_plugin

MAIN_COMMANDS = gather.Collector()

OTHER_COMMANDS = gather.Collector()


@MAIN_COMMANDS.register()
def main1(args: object) -> tuple[str, object]:
    """Register a plugin with the name of the function.

    Args:
        args: arbitrary payload echoed back.

    Returns:
        The plugin name paired with ``args``.
    """
    return "main1", args


@MAIN_COMMANDS.register(name="weird_name")
def main2(args: object) -> tuple[str, object]:
    """Register a plugin with an explicit name.

    Args:
        args: arbitrary payload echoed back.

    Returns:
        The plugin name paired with ``args``.
    """
    return "main2", args


@MAIN_COMMANDS.register(name="bar")
@OTHER_COMMANDS.register(name="weird_name")
def main3(args: object) -> tuple[str, object]:
    """Register a plugin for two collectors.

    Args:
        args: arbitrary payload echoed back.

    Returns:
        The plugin name paired with ``args``.
    """
    return "main3", args


@OTHER_COMMANDS.register(name="baz")
def main4(args: object) -> tuple[str, object]:
    """Register a plugin for the other collector.

    Args:
        args: arbitrary payload echoed back.

    Returns:
        The plugin name paired with ``args``.
    """
    return "main4", args


@_weird_plugin.weird_decorator
def weird_function() -> None:
    """Register a plugin using a wrapper function."""


TRANSFORM_COMMANDS = gather.Collector()


@TRANSFORM_COMMANDS.register(transform=gather.Wrapper.glue(5))
def fooish() -> None:
    """Register a plugin with a transformation."""


COLLIDING_COMMANDS = gather.Collector()

NON_COLLIDING_COMMANDS = gather.Collector()


@NON_COLLIDING_COMMANDS.register(name="weird_name")
@COLLIDING_COMMANDS.register(name="weird_name")
def weird_name1() -> None:
    """Register one of several commands for the same name."""


@COLLIDING_COMMANDS.register(name="weird_name")
def weird_name2() -> None:  # noqa: SLD801
    """Register one of several commands for the same name."""


@COLLIDING_COMMANDS.register(name="weird_name")
def weird_name3() -> None:  # noqa: SLD801
    """Register one of several commands for the same name."""


class CollectorTest(unittest.TestCase):
    """Tests for collecting plugins."""

    def test_collecting(self) -> None:
        """Collecting gives only the plugins for a given collector."""
        collected = unique(MAIN_COMMANDS.collect())
        self.assertIn("main1", collected)
        self.assertIs(collected["main1"], main1)
        self.assertNotIn("baz", collected)

    def test_non_collision(self) -> None:
        """Same name for different collectors does not collide."""
        main = unique(MAIN_COMMANDS.collect())
        other = unique(OTHER_COMMANDS.collect())
        self.assertIs(main["weird_name"], main2)
        self.assertIs(main["bar"], main3)
        self.assertIs(other["weird_name"], main3)

    def test_cross_module_collection(self) -> None:
        """Collection works for plugins registered in another module."""
        collected = unique(_weird_plugin.WEIRD_COMMANDS.collect())
        self.assertIn("weird_function", collected)

    def test_transform(self) -> None:
        """Collecting transformed plugins applies the transform."""
        collected = unique(TRANSFORM_COMMANDS.collect())
        self.assertIn("fooish", collected)
        res = cast(Wrapper, collected["fooish"])  # noqa: SLD203
        self.assertIs(res.original, fooish)
        self.assertEqual(res.extra, 5)

    def test_multiple(self) -> None:
        """Without unique, all plugins for a name are returned."""
        collected = dict(COLLIDING_COMMANDS.collect())
        weird_name = collected.pop("weird_name")
        self.assertEqual(collected, {})
        self.assertEqual(weird_name, {weird_name1, weird_name2, weird_name3})

    def test_multiple_unique_fails(self) -> None:
        """unique rejects a name with several registered plugins."""
        with self.assertRaises(ValueError):
            unique(COLLIDING_COMMANDS.collect())
