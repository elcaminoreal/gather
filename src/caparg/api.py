import importlib

import pkg_resources

import attr

import venusian

def _get_modules():
    for entry_point in pkg_resources.iter_entry_points(group='caparg'):
        module = importlib.import_module(entry_point.module_name)
        yield module

class Collector(object):

    def register(self, name=None):
        def callback(scanner, inner_name, ob):
            tag = getattr(scanner, 'tag', None)
            if tag is not self:
                return
            if name is None:
                effective_name = inner_name
            else:
                effective_name = name
            scanner.registry[effective_name] = ob 
        def ret(func):
            venusian.attach(func, callback)
            return func
        return ret

    def collect(self):
        registry = {}
        scanner = venusian.Scanner(registry=registry, tag=self)
        for module in _get_modules():
            scanner.scan(module)
        return registry

__all__ = ['Collector']
