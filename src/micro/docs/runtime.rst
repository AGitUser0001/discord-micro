Runtime and components
======================

A :class:`Runtime` is **one process's connection to a Micro deployment**: one NATS
connection with its JetStream context, the shared tables, the live presence directory, and
the :class:`Component` objects it hosts. Everything else (services, workers, the router)
is a component. The same components run in one runtime on a laptop or spread over many
runtimes on many machines; only configuration changes.

.. code-block:: python

   from micro.runtime import Runtime

   async with Runtime("nats://127.0.0.1:4222") as runtime:
     await runtime.add(service, worker)

   await Runtime().serve(service)       # until SIGTERM/SIGINT: drain, then close

.. list-table::
   :header-rows: 1
   :widths: 22 22 56

   * - Argument
     - Default
     - Meaning
   * - ``servers``
     - ``MICRO_NATS_URL``
     - One NATS URL or a list (comma separated in the variable). Default
       ``nats://127.0.0.1:4222``.
   * - ``name``
     - ``"micro"``
     - A label for this connection in logs and NATS.
   * - ``replicas``
     - 1
     - Replication of streams and buckets the runtime creates (use 3 on a NATS cluster).
   * - ``presence_ttl``
     - 10.0
     - Seconds before a component that stopped renewing disappears (at least 3).
   * - ``storage``
     - file
     - JetStream storage type (``StorageType.MEMORY`` in tests).
   * - ``**connect_options``
     -
     - Passed to ``nats.connect`` (credentials, TLS, reconnect settings).

Using a runtime
---------------

* ``await runtime.add(*components)`` starts components (starting the runtime if needed).
* ``async with`` starts and closes; ``await runtime.drain()`` drains components in reverse
  start order, each finishing its in-flight work; ``close()`` ends the connection.
* ``serve(*components)`` hosts them until ``SIGINT`` / ``SIGTERM``, then drains and closes.
  **A second signal skips the remaining drain.**
* ``runtime.nats`` and ``runtime.jetstream`` are the underlying clients, for advanced use.
* ``await runtime.table(bucket, ValueType)`` opens a typed table (:doc:`coordination`);
  ``await runtime.locks()`` the shared locks.
* ``await runtime.ensure_stream(...)`` creates a stream or brings an existing one up to date
  without losing data: missing subjects are added and ``retire``\ d ones removed, so a rolling
  upgrade of Micro can move subjects between streams.
* ``runtime.request(...)`` / ``respond(...)`` / ``payload(...)`` are NATS request and reply
  that work for bodies **larger than the server's message limit**: a large body travels through
  a NATS object store (``micro_payloads``) and is fetched and deleted by the receiver, invisibly.

The event loop
~~~~~~~~~~~~~~

:func:`event_loop_factory` returns the fastest installed loop: ``uvloop`` (Linux, macOS),
``winloop`` (Windows) or asyncio's own. Install both with the ``accel`` extra. The CLI uses it.

Components
----------

A :class:`Component` is anything a runtime hosts. Its lifecycle is

``start`` → running → ``drain`` (stop taking new work, finish in-flight work, release leases)
→ ``close``

Subclasses override the hooks and use ``spawn`` for background tasks and ``tracked`` around
each unit of work.

.. code-block:: python

   import asyncio
   from micro.runtime import Component

   class Ticker(Component):
     async def on_start(self) -> None:
       self.spawn(self.tick(), name="tick")      # cancelled on close, failures are logged

     async def tick(self) -> None:
       while self.active:                        # False once draining
         async with self.tracked():              # drain waits for this to finish
           ...
         await asyncio.sleep(60)

* ``on_start`` / ``on_drain`` / ``on_close`` are the hooks. ``runtime`` is set once started.
* ``active`` is true while work sources should keep handing out new work; ``accepting`` is
  whether ``tracked`` will still take work (it raises :class:`DrainingError` after close).
* ``ready`` says whether the component can serve now (the HTTP bridge's readiness probe
  asks); subclasses may add checks.
* ``in_flight`` counts tracked work. ``phase`` is the :class:`ComponentState`.

Presence and discovery
----------------------

Components advertise themselves in the ``micro_presence`` bucket with a TTL that they keep
renewing; a crashed one disappears on its own. Other components read the live
:class:`Directory`, which is kept up to date by watching the table.

.. code-block:: python

   presence = await runtime.register(component, metadata={"zone": "eu"})
   await presence.update({"zone": "us"})               # change the metadata
   runtime.directory.entries("service")                # live Registrations of a kind
   runtime.directory.on_change(callback)               # any change
   runtime.directory.on_change(callback, watching=lambda: runtime.directory.entries("http"))
   await runtime.directory.wait_for(lambda d: bool(d.entries("gateway")))

``on_change(listener, watching=...)`` exists because presence entries refresh constantly:
passing a function that returns the part you care about makes the listener run only when
*that part* changes. A :class:`Registration` has the ``kind``, ``name``, hosting ``instance``,
a unique ``id`` (which doubles as the component's routing address) and its ``metadata``.

Durable stream consumers
------------------------

:class:`StreamConsumer` is the engine behind events, work queues and interaction routes: **one
durable consumer shared by every replica** of a logical component, each message going to one
of them.

* A handler that returns acknowledges the message.
* ``raise Retry(delay)`` redelivers it after ``delay`` seconds; ``raise Reject`` drops it for
  good; any other exception redelivers it after a backoff (:func:`default_backoff`: 1, 2, 4, ...
  seconds up to 60).
* Long handlers keep their message alive with progress acknowledgements, so there is **no
  handler deadline**.
* ``ack_first=True`` acknowledges *before* the handler runs: **at-most-once**, never
  redelivered. Interactions use this, because they can be answered only once.
* It fetches one message at a time and runs up to ``concurrency`` handlers.
* ``deliver_new=True`` (the default) starts a new consumer at "now"; ``False`` starts it from
  the beginning of what the stream still holds (work queues).

Reference
---------

.. api::
   micro.runtime.Runtime
   micro.runtime.Component
   micro.runtime.ComponentState
   micro.runtime.Directory
   micro.runtime.Presence
   micro.runtime.Registration
   micro.runtime.StreamConsumer
   micro.runtime.Retry
   micro.runtime.Reject
   micro.runtime.Reply
   micro.runtime.default_backoff
   micro.runtime.default_servers
   micro.runtime.event_loop_factory
   micro.runtime.DEFAULT_NATS_URL
   micro.runtime.PAYLOAD_HEADER
   micro.runtime.RUNTIME_KIND
