.. Copyright (c) Moshe Zadka
   See LICENSE for details.

Gather
======

.. toctree::
   :maxdepth: 2

Overview
--------

The :code:`gather` package allows gathering up plugins.

Entry points
~~~~~~~~~~~~

Gathering depends on
registering an entry point in the
package.
For example,
with
:code:`pyproject.toml`:

.. code::

    [project.entry-points.gather]
    ignored = "<ROOT_PACKAGE>"

Putting the package name there is enough -- :code:`gather`
will automatically collect from any sub-modules,
recursing any number of levels.
These entry points are enough regardless of the plugin collector:
collectors will only collect their own plugins.

Collectors
~~~~~~~~~~

A
:code:`Collector`
represents a
"kind of plugin".
It is an object,
usually defined at the top level of a module:

.. code::

    import gather
    THINGS = gather.Collector()

Collecting all registered functions:

.. code::

    registered = THINGS.collect()

The return value is a dictionary,
mapping names to sets of registered functions.

The function
:code:`gather.unique`
takes a dictionary,
and returns a dictionary
mapping names to registered functions.
It will raise a
:code:`ValueError`
if multiple functions are registered to the same name.

Registering
~~~~~~~~~~~

In order to register a function as a plugin,
decorate it using the relevant collector:

.. code::

    @THINGS.register()
    def some_function():
        pass

The decorator always returns the function
without modification.
This allows,
for example,
using
:code:`some_function`
in a unit test.

If an alternative name is needed for registration,
one can be provided explicitly:

.. code::

    @THINGS.register(name='register_as_this_name')
    def generic():
        pass

Transforms
~~~~~~~~~~

Depending on the collector,
it might expect some extra data.
This should be documented as part of the collector.
Supplying the data is done with the
:code:`transform` argument:

.. code::

    @THINGS.register(
        name='register_as_this_name',
        transform=things_transformer(flexibility=5),
    )
    def generic():
        pass

The collector can define a transformer using
:code:`gather.Wrapper`:

.. code::

    def things_transformer(flexibility):
        return gather.Wrapper.glue(flexibility)

When collecting,
the value in the mapping returned in
:code:`.collect()`
will be an object.
The
:code:`.original`
attribute will be the function.
The
:code:`.extra`
will be the arguments given to the
:code:`glue`
function:
in this case,
for
:code:`register_as_name`,
it will be
:code:`5`.


API
---

Plugins
~~~~~~~~~~

.. automodule:: gather.api
   :members:

Command dispatch
~~~~~~~~~~~~~~~~

.. automodule:: gather.commands
   :members: add_argument, make_command_register, set_parser

   .. autofunction:: run(*, parser, argv=sys.argv, env=os.environ, sp_run=subprocess.run)

Script entry points
~~~~~~~~~~~~~~~~~~~

.. automodule:: gather.entry
   :members:
