"""Gather -- Collect all your plugins

Gather allows a way to register plugins.
It features the ability to register the plugins from any module,
in any package, in any distribution.
A given module can register plugins of multiple types.

In order to have anything registered from a package,
it needs to declare that it supports :code:`gather` in its `setup.py`:

.. code::

    entry_points={
        'gather': [
             "dummy=ROOT_PACKAGE:dummy",
        ]

The :code:`ROOT_PACKAGE` should point to the Python name of the package:
i.e., what users are expected to :code:`import` at the top-level.

Note that while having special facilities to run functions as subcommands,
Gather can be used to collect anything.
"""
from __future__ import print_function

import importlib
import sys

import pkg_resources

import attr

import venusian

def _get_modules():
    for entry_point in pkg_resources.iter_entry_points(group='gather'):
        module = importlib.import_module(entry_point.module_name)
        yield module


@attr.s(frozen=True)
class Collector(object):

    """A plugin collector.

    A collector allows to *register* functions or classes by modules,
    and *collect*-ing them when they need to be used.
    """

    name = attr.ib(default=None)

    depth = attr.ib(default=1)

    @staticmethod
    def one_of(registry, effective_name, objct):
        return objct

    @staticmethod
    def all(registry, effective_name, objct):
        st = registry.get(effective_name, set())
        st.add(objct)
        return st

    @staticmethod
    def conflict(registry, effective_name, objct):
        if effective_name in registry:
            raise ValueError("Attempt to double register",
                             registry, effective_name, objct)
        return objct

    def register(self, name=None, transform=lambda x: x):
        """Register

        :param name: optional. Name to register as (default is name of object)
        :param transform: optional. A one-argument function. Will be called,
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
            tag = getattr(scanner, 'tag', None)
            if tag is not self:
                return
            if name is None:
                effective_name = inner_name
            else:
                effective_name = name
            objct = transform(objct)
            try:
                scanner.registry[effective_name] = scanner.strategy(scanner.registry, effective_name, objct)
            except ValueError as exc:
                scanner.please_raise = exc
        def ret(func):
            venusian.attach(func, callback, depth=self.depth)
            return func
        return ret

    def collect(self, strategy=one_of.__func__):
        """Collect all registered.

        Returns a dictionary mapping names to registered elements.
        """
        registry = {}
        def ignore_import_error(_unused):
            if not issubclass(sys.exc_info()[0], ImportError):
                raise # pragma: no cover
        scanner = venusian.Scanner(registry=registry, tag=self, strategy=strategy)
        for module in _get_modules():
            scanner.scan(module, onerror=ignore_import_error)
        if hasattr(scanner, 'please_raise'):
            raise scanner.please_raise
        return registry

def run(argv, commands, version, output):
    """Run the correct subcommand.

    :param argv: Arguments to be processed
    :type argv: List of strings
    :param commands: Commands (usually collected by a :code:`Collector`)
    :type commands: Mapping of strings to functions that accept arguments
    :param str version: Version string to display
    :param file output: Where to write output to
    """
    if len(argv) < 1:
        argv = argv + ['help']
    if argv[0] in ('version', '--version'):
        print("Version {}".format(version), file=output)
        return
    if argv[0] in ('help', '--help') or argv[0] not in commands:
        print("Available subcommands:", file=output)
        for command in commands.keys():
            print("\t{}".format(command), file=output)
        print("Run subcommand with '--help' for more information", file=output)
        return
    commands[argv[0]](argv)

@attr.s(frozen=True)
class Wrapper(object):

    """Add extra data to an object"""

    original = attr.ib()

    extra = attr.ib()

    @classmethod
    def glue(cls, extra):
        """Glue extra data to an object

        :param extra: what to add
        :returns: function of one argument that returns a :code:`Wrapped`

        This method is useful mainly as the :code:`transform` parameter
        of a :code:`register` call.
        """
        def ret(original):
            return cls(original=original, extra=extra)
        return ret

__all__ = ['Collector', 'run', 'Wrapper']
