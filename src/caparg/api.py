"""CapArg -- Captain Arguments, Ready for Sub-Command!

CapArg (Captain Arguments) allows a way to register sub-commands
for a command.
It features the ability to register the sub-commands from any module,
in any package, in any distribution.
A given module can register sub-commands for multiple commands.

In order to have anything registered from a package,
it needs to declare that it supports :code:`caparg` in its `setup.py`:

.. code::

    entry_points={
        'caparg': [
             "dummy=ROOT_PACKAGE:dummy",
        ]

The :code:`ROOT_PACKAGE` should point to the Python name of the package:
i.e., what users are expected to :code:`import` at the top-level.

Note that while having special facilities to run functions as subcommands,
CapArg can be used to collect anything.
This allows it to serve as a generic plugin module.
"""
from __future__ import print_function

import importlib
import sys

import pkg_resources

import venusian

def _get_modules():
    for entry_point in pkg_resources.iter_entry_points(group='caparg'):
        module = importlib.import_module(entry_point.module_name)
        yield module

class Collector(object):

    """A plugin collector.

    A collector allows to *register* functions or classes by modules,
    and *collect*-ing them when they need to be used.
    """

    def register(self, name=None):
        """Register

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
            scanner.registry[effective_name] = objct
        def ret(func):
            venusian.attach(func, callback)
            return func
        return ret

    def collect(self):
        """Collect all registered.

        Returns a dictionary mapping names to registered elements.
        """
        registry = {}
        def ignore_import_error(_unused):
            if not issubclass(sys.exc_info()[0], ImportError):
                raise # pragma: no cover
        scanner = venusian.Scanner(registry=registry, tag=self)
        for module in _get_modules():
            scanner.scan(module, onerror=ignore_import_error)
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

__all__ = ['Collector', 'run']
