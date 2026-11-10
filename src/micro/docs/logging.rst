Logging
=======

``micro.log`` is the logging to use, in your code and in Micro's. There is nothing to set up:

.. code-block:: python

   from micro import log

   log.info("sent report", guild=guild_id, channel=channel_id)
   log.warning("rate limited, retrying in %.1fs", delay, route=route)
   log.error("could not edit", error=error)
   log.exception("handler failed")          # inside an ``except``: adds the traceback

   mine = log.bind(user=user.id)            # a logger that carries these fields
   mine.info("joined")

It is the standard ``logging`` underneath, so one handler, one level setting
(``micro run -v``) and one ``logging.config`` still cover Micro, hikari, nats and your own code
alike. What it adds is that you never write ``getLogger(__name__)`` and that a line says
more than its text.

The logger name
---------------

``log`` takes the name of the module it is called from, so ``micro.service._service`` and
``myapp.cogs.tickets`` are separate loggers you can filter, and the file and line shown are
the caller's.

Fields
------

Keyword arguments are **fields**: ``log.info("sent", guild=1)`` writes
``sent  guild=1``, and also keeps ``{"guild": 1}`` on the record as ``record.fields`` for a
handler that writes JSON. ``log.bind(...)`` returns a logger with fields attached, and

.. code-block:: python

   with log.context(guild=guild_id):
       ...                                   # every line made meanwhile has guild=...

puts them on every line made inside the block, including lines made by tasks that block
starts. ``%``-style arguments work as in the standard library.

The call path
-------------

Every line also carries the logical **path** of the work that made it, outermost first:

.. code-block:: text

   ERROR micro.discord: could not edit  path=tickets > interaction ticket.close > archive thread  interaction=1234 error=NotFound(10008)

Micro sets the first segments while a handler runs: the service, then the request, event,
job or interaction. Add your own with ``step``:

.. code-block:: python

   with log.step("archive thread"):
       ...

   @log.step("render report")               # also on an async function
   async def render(...): ...

A step also logs, at DEBUG, how long it took, and says ``failed`` if it raised. The path
and the fields live in context variables rather than the call stack, so they follow the
work into every task it starts, which a stack of frames cannot do.

Error results nobody looked at
------------------------------

Dropping an :class:`Err` (writing ``await message.delete()`` on a line of its own) would
hide a failure that an exception could not. Micro reports it two ways, and both name the
error and **where the result was created** (the file, line and function, innermost first):

* While a handler runs, an ``Err`` that is still unlooked-at when the handler finishes
  fails the handler with :class:`UnhandledResult`, the way an exception would: logged, a
  "Something went wrong" for an interaction, a retry for an event, ``handler_failed`` for a
  request. An exception the handler itself raised stands on its own.
* Anywhere else (a script, a task nobody awaits) it is logged at ERROR when the ``Err`` is
  garbage collected. A log line is all that is possible there, since nothing can be
  raised from a finalizer.

An ``Err`` counts as looked at when you use it in any way: ``unwrap``, ``ok``,
``unwrap_or``, ``ignore``, ``map``, ``is_ok`` / ``is_err``, or read ``.error`` (which is
what ``match`` does).

Reference
---------

.. api::
   micro.log.debug
   micro.log.info
   micro.log.warning
   micro.log.error
   micro.log.critical
   micro.log.exception
   micro.log.log
   micro.log.enabled
   micro.log.bind
   micro.log.context
   micro.log.step
   micro.log.path
   micro.log.fields
   micro.log.Logger
   micro.log.Span
