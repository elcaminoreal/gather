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


class GatherCollisionError(ValueError):
    """Two or more plugins registered for the same name."""


def _one_of(_registry, _effective_name, objct):
    """
    Assign one of the possible options.

    When given as a collection strategy to :code:`collect`,
    this will assign one of the options to a name in case more
    than one item is registered to the same name.

    This is the default.
    """
    return objct


def _all(registry, effective_name, objct):
    """
    Assign all of the possible options.

    Collect all registered items into a set,
    and assign that set to a name. Note that
    even if only one item is assigned to a name,
    that name will be assigned to a set of length 1.
    """
    myset = registry.get(effective_name, set())
    myset.add(objct)
    return myset


def _exactly_one(registry, effective_name, objct):
    """
    Raise an error on colliding registration.

    If more than one item is registered to the
    same name, raise a :code:`GatherCollisionError`.
    """
    if effective_name in registry:
        raise GatherCollisionError(
            "Attempt to double register", registry, effective_name, objct
        )
    return objct


@attr.s(frozen=True)
class Collector(object):

    """
    A plugin collector.

    A collector allows to *register* functions or classes by modules,
    and *collect*-ing them when they need to be used.
    """

    name = attr.ib(default=None)

    depth = attr.ib(default=1)

    one_of = staticmethod(_one_of)

    all = staticmethod(_all)

    exactly_one = staticmethod(_exactly_one)

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
            scanner.update(effective_name, objct)

        def attach(func):
            """Attach callback to be called when object is scanned"""
            venusian.attach(func, callback, depth=self.depth)
            return func

        return attach

    def collect(self, strategy=one_of.__func__):
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

        params = _ScannerParameters(strategy=strategy)
        scanner = venusian.Scanner(update=params.update, tag=self)
        for module in _get_modules():
            # Venusian is using a newly-deprecated method to scan modules
            with _ignore_deprecation():
                scanner.scan(module, onerror=ignore_import_error)
        params.raise_if_needed()
        return params.registry


@attr.s
class _ScannerParameters(object):

    """
    Parameters for scanner

    Update the registry respecting the strategy,
    and raise errors at the end.
    """

    _please_raise = attr.ib(init=False, default=None)
    _strategy = attr.ib()
    registry = attr.ib(init=False, default=attr.Factory(dict))

    def update(self, name, objct):
        """Update registry with name->objct"""
        try:
            res = self._strategy(self.registry, name, objct)
            self.registry[name] = res
        except GatherCollisionError as exc:
            self._please_raise = exc

    def raise_if_needed(self):
        """Raise exception if any of the updates failed."""
        if self._please_raise is not None:
            raise self._please_raise


def run(argv, commands, version, output):
    """
    Run the specified subcommand.

    Args:
        argv (list of str): Arguments to be processed
        commands (mapping of str to callables): Commands (usually collected by a :code:`Collector`)
        version (str): Version to display if :code:`--version` is asked
        output (file): Where to write output to
    """
    if len(argv) < 1:
        argv = argv + ["help"]
    if argv[0] in ("version", "--version"):
        output.write("Version {}\n".format(version))
        return
    if argv[0] in ("help", "--help") or argv[0] not in commands:
        output.write("Available subcommands:\n")
        for command in commands.keys():
            output.write("\t{}\n".format(command))
        output.write("Run subcommand with '--help' for more information\n")
        return
    commands[argv[0]](argv)


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


__all__ = ["Collector", "run", "Wrapper"]
