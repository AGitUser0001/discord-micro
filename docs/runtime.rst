Runtime and components
======================

``Runtime`` is one process's NATS connection. It hosts any number of
components and owns the shared tables and the presence directory.

.. code-block:: python

   from micro.runtime import Runtime

   async with Runtime("nats://127.0.0.1:4222") as runtime:   # or MICRO_NATS_URL
     await runtime.add(service, worker)

   await Runtime().serve(service)   # until SIGTERM: drain, then close

``Runtime(replicas=3)`` creates streams and buckets with R3 replication.

Components
----------

Lifecycle: ``start → running → drain → close``. Draining stops new work,
finishes in-flight work, and releases leases. ``serve`` drains on the first
SIGINT/SIGTERM and closes on a second.

.. code-block:: python

   from micro.runtime import Component

   class Ticker(Component):
     async def on_start(self) -> None:
       self.spawn(self.tick(), name="tick")      # cancelled on close

     async def tick(self) -> None:
       while self.active:                        # false once draining
         async with self.tracked():              # drain waits for this
           ...
         await asyncio.sleep(60)

Hooks: ``on_start``, ``on_drain``, ``on_close``. Properties: ``phase``,
``active``, ``accepting``, ``ready``, ``runtime``.

Presence and discovery
----------------------

Components advertise themselves in the ``micro_presence`` bucket with a TTL;
crashed ones disappear automatically.

.. code-block:: python

   presence = await runtime.register(component, metadata={"zone": "eu"})
   runtime.directory.entries("service")              # live registrations
   runtime.directory.on_change(callback)
   await runtime.directory.wait_for(lambda d: bool(d.entries("gateway")))

Durable stream consumers
------------------------

``StreamConsumer`` is the engine behind events, work queues, and interaction
routes: one durable consumer shared by every replica, progress acks for long
handlers, ``Retry(delay)`` to redeliver, ``Reject`` to drop, and
``ack_first=True`` for at-most-once work.
