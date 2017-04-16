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

    def register(self, name=None):
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
        registry = {}
        def ignore_import_error(_unused):
            if not issubclass(sys.exc_info()[0], ImportError):
                raise # pragma: no cover
        scanner = venusian.Scanner(registry=registry, tag=self)
        for module in _get_modules():
            scanner.scan(module, onerror=ignore_import_error)
        return registry

def run(argv, commands, version, output):
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

__all__ = ['Collector']
