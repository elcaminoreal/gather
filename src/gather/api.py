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
import contextlib
import importlib.metadata
import sys
import warnings

import attr
import venusian


@contextlib.contextmanager
def _ignore_deprecation():
    warnings.filterwarnings(action="ignore", category=DeprecationWarning)
    try:
        yield
    finally:
        warnings.filters.pop(0)


def _get_modules():
    eps = importlib.metadata.entry_points()
    with _ignore_deprecation():
        gather_points = eps["gather"]
    for entry_point in gather_points:
        module = importlib.import_module(entry_point.value)
        yield module


@attr.s(frozen=True)
class Collector(object):

    """
    A plugin collector.

    A collector allows to *register* functions or classes by modules,
    and *collect*-ing them when they need to be used.
    """

    name = attr.ib(default=None)

    depth = attr.ib(default=1)

    def register(self, name=None, transform=lambda x: x):
        """
        Register a class or function

        Args:
            name (str): optional. Name to register the class or function as.
                        (default is name of object)
            transform (callable): optional. A one-argument function. Will be called,
                          and the return value used in collection.
                          Default is identity function

        This is meant to be used as a decoator:

        .. code::

            @COLLECTOR.register()
            def specific_subcommand(args):
                pass

            @COLLECTOR.register(name='another_specific_name')
            def main(args):
                pass
        """

        def callback(scanner, inner_name, objct):
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

        def attach(func):
            """Attach callback to be called when object is scanned"""
            venusian.attach(func, callback, depth=self.depth)
            return func

        return attach

    def collect(self):
        """
        Collect all registered functions or classes.

        Returns a dictionary mapping names to registered elements.
        """

        def ignore_import_error(_unused):
            """
            Ignore ImportError during collection.

            Some modules raise import errors for various reasons,
            and should be just treated as missing.
            """
            if not issubclass(sys.exc_info()[0], ImportError):
                raise  # pragma: no cover

        registry = collections.defaultdict(set)
        scanner = venusian.Scanner(registry=registry, tag=self)
        for module in _get_modules():
            # Venusian is using a newly-deprecated method to scan modules
            with _ignore_deprecation():
                scanner.scan(module, onerror=ignore_import_error)
        return registry


def unique(mapping):
    """
    Transform map to sets to map to single items.

    Raises a :code:`ValueError` if any of the values is not an iterable
    with exactly one item.

    Args:
        mapping: A mapping of keys to Iterables of 1

    Returns:
        A mapping of keys to the single value
    """
    ret = {}
    for key, value_set in mapping.items():
        [value] = value_set
        ret[key] = value
    return ret


@attr.s(frozen=True)
class Wrapper(object):

    """Add extra data to an object"""

    original = attr.ib()

    extra = attr.ib()

    @classmethod
    def glue(cls, extra):
        """
        Glue extra data to an object

        Args:
            extra: what to add

        Returns:
            callable: function of one argument that returns a :code:`Wrapped`

        This method is useful mainly as the :code:`transform` parameter
        of a :code:`register` call.
        """

        def ret(original):
            """Return a :code:`Wrapper` with the original and extra"""
            return cls(original=original, extra=extra)

        return ret


__all__ = ["Collector", "unique", "Wrapper"]
