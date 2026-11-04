Coordination
============

Typed tables
------------

NATS KV with compare-and-set and per-key TTLs.

.. code-block:: python

   from micro import subjects

   table = await runtime.table(subjects.STATE_BUCKET, Counter)
   revision = await table.create("count", Counter(value=1))          # None if it exists
   await table.update("count", Counter(value=2), revision=revision)  # None on conflict
   await table.put_with_ttl("heartbeat", Counter(value=0), ttl=10)
   current = await table.get("count")          # Versioned(value, revision) | None
   items = await table.items("prefix.>")
   async for change in table.watch(): ...       # None once caught up, then changes

Locks
-----

.. code-block:: python

   locks = await runtime.locks()
   await locks.gate("identify.0", ttl=5)        # at most one caller per 5 s
   async with locks.hold("nightly-job", ttl=30):  # renewed while held
     ...

Declarations
------------

Versioned documents that converge across rolling updates; commands and graph
modules use them.

.. code-block:: python

   from micro.coordination import Declarations

   declarations = Declarations(runtime, "commands")
   view = await declarations.view()     # {key: Declared(hash, document, state)}
   await declarations.mark_applied(key, view[key].hash)
   await declarations.forget(key)       # retire a key

States: ``converged`` (all live declarers agree), ``mixed`` (rollout running;
the applied version stands), ``retained`` (nobody declares it right now; kept
until forgotten). Two versions arriving at once wait until they converge.
