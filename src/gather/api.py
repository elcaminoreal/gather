"""Gather -- Collect all your plugins

Gather allows a way to register plugins.
It features the ability to register the plugins from any module,
in any package, in any distribution.
A given module can register plugins of multiple types.

In order to have anything registered from a package,
it needs to declare that it supports :code:`gather`
in its package metadata.

For example,
with
:code:`pyproject.toml`:

.. code::

    [project.entry-points.gather]
    ignored = "<ROOT_PACKAGE>"


The :code:`ROOT_PACKAGE` should point to the Python name of the package:
i.e., what users are expected to :code:`import` at the top-level.

Note that while having special facilities to run functions as subcommands,
Gather can be used to collect anything.
"""

import collections
import importlib
import importlib.metadata
import sys
from types import ModuleType
from typing import Callable, Iterable, Iterator, Mapping, TypeVar

import attrs
import venusian

_T = TypeVar("_T")
_V = TypeVar("_V")


def _get_modules() -> Iterator[ModuleType]:
    for entry_point in importlib.metadata.entry_points(group="gather"):
        module = importlib.import_module(entry_point.value)
        yield module


def _identity(obj: _T) -> _T:
    """Return the argument unchanged."""
    return obj


@attrs.frozen
class Collector:
    """
    A plugin collector.

    A collector allows to *register* functions or classes by modules,
    and *collect*-ing them when they need to be used.
    """

    name: str | None = None

    depth: int = 1

    def register(
        self,
        name: str | None = None,
        transform: Callable[[object], object] = _identity,
    ) -> Callable[[_T], _T]:
        """
        Register a class or function

        Args:
            name (str): optional. Name to register the class or function as.
                        (default is name of object)
            transform (callable): optional. A one-argument function. Will be called,
                          and the return value used in collection.
                          Default is identity function

        Returns:
            A decorator that attaches the registration to its argument.

        This is meant to be used as a decoator:

        .. code::

            @COLLECTOR.register()
            def specific_subcommand(args):
                pass

            @COLLECTOR.register(name='another_specific_name')
            def main(args):
                pass
        """

        def callback(scanner: venusian.Scanner, inner_name: str, objct: object) -> None:
            (
                """
            Venusian_ callback, called from scan

            .. _Venusian: http://docs.pylonsproject.org/projects/"""
                """venusian/en/latest/api.html#venusian.attach
            """
            )
            tag = getattr(scanner, "tag", None)
            if tag is not self:
                return
            if name is None:
                effective_name = inner_name
            else:
                effective_name = name
            objct = transform(objct)
            scanner.registry[effective_name].add(objct)

        def attach(func: _T) -> _T:
            """Attach callback to be called when object is scanned"""
            venusian.attach(func, callback, depth=self.depth)
            return func

        return attach

    def collect(self) -> "collections.defaultdict[str, set[object]]":
        """
        Collect all registered functions or classes.

        Returns:
            A dictionary mapping names to registered elements.
        """

        def ignore_import_error(_unused: object) -> None:
            """
            Ignore ImportError during collection.

            Some modules raise import errors for various reasons,
            and should be just treated as missing.
            """
            exc_type = sys.exc_info()[0]
            if exc_type is None or not issubclass(exc_type, ImportError):
                raise  # pragma: no cover

        registry: "collections.defaultdict[str, set[object]]" = collections.defaultdict(
            set
        )
        scanner = venusian.Scanner(registry=registry, tag=self)
        for module in _get_modules():
            scanner.scan(module, onerror=ignore_import_error)
        return registry


def unique(mapping: Mapping[_T, Iterable[_V]]) -> dict[_T, _V]:
    """
    Transform map to sets to map to single items.

    Raises a :code:`ValueError` if any of the values is not an iterable
    with exactly one item.

    Args:
        mapping: A mapping of keys to Iterables of 1

    Returns:
        A mapping of keys to the single value
    """
    ret: dict[_T, _V] = {}
    for key, value_set in mapping.items():
        [value] = value_set
        ret[key] = value
    return ret


@attrs.frozen
class Wrapper:
    """Add extra data to an object"""

    original: object

    extra: object

    @classmethod
    def glue(cls, extra: object) -> Callable[[object], "Wrapper"]:
        """
        Glue extra data to an object

        Args:
            extra: what to add

        Returns:
            callable: function of one argument that returns a :code:`Wrapped`

        This method is useful mainly as the :code:`transform` parameter
        of a :code:`register` call.
        """

        def ret(original: object) -> "Wrapper":
            """Return a :code:`Wrapper` with the original and extra"""
            return cls(original=original, extra=extra)

        return ret


__all__ = ["Collector", "unique", "Wrapper"]
