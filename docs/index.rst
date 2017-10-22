.. Copyright (c) Moshe Zadka
   See LICENSE for details.

Gather
======

.. toctree::
   :maxdepth: 2

Overview
--------

The :code:`gather` package allows easily gathering up plugins.
The basic class defined is the :code:`Collector`.

.. code::

    import gather
    THINGS = gather.Collector()

In order to register an object as a plugin, we merely decorate it:

.. code::

    @THINGS.register()
    def some_function():
        pass

Note that the decorator always returns the function --
:code:`some_function` remains perfectly usable.

Finding all the things collected is simple:

.. code::

    registered = THINGS.collect()

The return value is a dictionary,
mapping names to registered objects.

If an alternative name is needed for registration,
one can be provided explicitly:

.. code::

    @THINGS.register(name='register_as_this_name')
    def generic():
        pass

When registering functions that expect an argument list,
like :code:`sys.argv`,
the :code:`run` function can be used to run them directly:

.. code::

    gather.run(
        commands=THINGS.collect(),
        version='1.2.3',
        argv=sys.argv[1:],
        output=sys.stdout
    )

It is important to remember that all the gathering depends on
registering an entry point in the :code:`setup.py`:

.. code::

    entry_points={
        'gather': [
             "gather=ROOT_PACKAGE",
        ]

Putting the package name there is enough -- :code:`gather`
will automatically collect from any sub-modules,
recursing any number of levels.
This is also enough to register it for any :code:`gather`-using plugins.


API
---
.. automodule:: gather.api
   :members:
