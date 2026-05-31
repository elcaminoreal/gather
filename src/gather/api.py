"""Gather -- Collect all your plugins.

Gather allows a way to register plugins.
It features the ability to register the plugins from any module,
in any package, in any distribution.
A given module can register plugins of multiple types.

In order to have anything registered from a package,
it needs to declare that it supports ``gather``
in its package metadata.
For example, with ``pyproject.toml`` an entry point named ``gather``
should point ``<ROOT_PACKAGE>`` at the Python name of the package --
what users are expected to ``import`` at the top level.

Note that while having special facilities to run functions as subcommands,
Gather can be used to collect anything.
"""

import collections
import dataclasses
import importlib
import importlib.metadata
import sys
from types import ModuleType
from typing import Callable, Iterable, Iterator, Mapping, TypeVar

import venusian

_Key = TypeVar("_Key")
_Value = TypeVar("_Value")
_Element = TypeVar("_Element")


def _get_modules() -> Iterator[ModuleType]:
    for entry_point in importlib.metadata.entry_points(group="gather"):
        module = importlib.import_module(entry_point.value)
        yield module


# Identity transform: returns its argument unchanged.
def _identity(obj: _Element) -> _Element:
    return obj


def _ignore_import_error(_unused: object) -> None:
    # venusian onerror callback: swallow ImportError, re-raise anything else.
    exc_type = sys.exc_info()[0]
    if exc_type is None or not issubclass(exc_type, ImportError):
        raise  # pragma: no cover


@dataclasses.dataclass(frozen=True)
class Collector:
    """A plugin collector.

    A collector allows to *register* functions or classes by modules,
    and *collect*-ing them when they need to be used.

    Attributes:
        name: an optional name for the collector.
        depth: the venusian scan depth used when attaching registrations.
    """

    name: str | None = None
    depth: int = 1

    def register(  # noqa: SLD303
        self,
        name: str | None = None,
        transform: Callable[[object], object] = _identity,
    ) -> Callable[[_Element], _Element]:
        """Register a class or function.

        This is meant to be used as a decorator::

            @COLLECTOR.register()
            def specific_subcommand(args):
                pass

            @COLLECTOR.register(name='another_specific_name')
            def main(args):
                pass

        Args:
            name: optional name to register the object as
                (defaults to the name of the object).
            transform: optional one-argument function whose return value is
                used in collection (defaults to the identity function).

        Returns:
            A decorator that attaches the registration to its argument.
        """

        def callback(scanner: venusian.Scanner, inner_name: str, objct: object) -> None:
            """Attach the registration when venusian scans the object.

            Args:
                scanner: the venusian scanner driving the scan.
                inner_name: the name the object was defined as.
                objct: the object being registered.
            """
            if getattr(scanner, "tag", None) is not self:
                return
            effective_name = inner_name if name is None else name
            scanner.registry[effective_name].add(transform(objct))

        def attach(func: _Element) -> _Element:
            """Attach the callback to be called when the object is scanned.

            Args:
                func: the object being registered.

            Returns:
                The argument, unchanged.
            """
            venusian.attach(func, callback, depth=self.depth)
            return func

        return attach

    def collect(  # noqa: SLD303
        self,
    ) -> Mapping[str, "set[object]"]:
        """Collect all registered functions or classes.

        Returns:
            A mapping of names to sets of registered elements.
        """
        registry: "collections.defaultdict[str, set[object]]" = collections.defaultdict(
            set
        )
        scanner = venusian.Scanner(registry=registry, tag=self)
        for module in _get_modules():
            scanner.scan(module, onerror=_ignore_import_error)
        return registry


def unique(mapping: Mapping[_Key, Iterable[_Value]]) -> Mapping[_Key, _Value]:
    """Transform a map-to-iterables into a map-to-single-items.

    Args:
        mapping: a mapping of keys to iterables of exactly one item.

    Returns:
        A mapping of keys to the single value.

    Raises:
        ValueError: if any of the values is not an iterable with exactly
            one item.
    """
    ret: dict[_Key, _Value] = {}
    for key, value_set in mapping.items():
        [value] = value_set
        ret[key] = value
    return ret


@dataclasses.dataclass(frozen=True)
class Wrapper:
    """Add extra data to an object.

    Attributes:
        original: the wrapped object.
        extra: the extra data glued to the object.
    """

    original: object
    extra: object

    @classmethod
    def glue(cls, extra: object) -> Callable[[object], "Wrapper"]:
        """Glue extra data to an object.

        This method is useful mainly as the ``transform`` parameter
        of a ``register`` call.

        Args:
            extra: what to add.

        Returns:
            A function of one argument that returns a ``Wrapper``.
        """

        def ret(original: object) -> "Wrapper":
            """Return a ``Wrapper`` with the original and extra.

            Args:
                original: the object to wrap.

            Returns:
                A ``Wrapper`` of original and the glued extra.
            """
            return cls(original=original, extra=extra)

        return ret


__all__ = ["Collector", "unique", "Wrapper"]
