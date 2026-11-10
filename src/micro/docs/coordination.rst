Coordination
============

Micro needs no coordinator process. The few things that must agree across processes (who
holds a lock, which version of a declaration is live, a counter, a lease) are kept in NATS
JetStream key-value buckets, and ``micro.coordination`` is the typed way to use them.

Tables
------

A :class:`Table` is a typed key/value bucket with compare-and-set and per-key time to live.
Values are validated by Pydantic in both directions, so a table of ``Counter`` models only
ever holds and returns ``Counter``.

.. code-block:: python

   from micro import subjects

   table = await runtime.table(subjects.STATE_BUCKET, Counter)
   revision = await table.create("count", Counter(value=1))          # None if it exists
   await table.update("count", Counter(value=2), revision=revision)  # None on conflict
   await table.put_with_ttl("heartbeat", Counter(value=0), ttl=10)   # expires by itself
   current = await table.get("count")          # Versioned(value, revision) | None
   items = await table.items("prefix.>")       # {key: Versioned}
   await table.delete("count", revision=revision)
   async for change in table.watch(): ...       # current values, then None once caught up, then changes

* **Revisions are the compare-and-set token.** ``update(key, value, revision=r)`` succeeds
  only if the key is still at revision ``r``; ``create`` only if the key does not exist.
  Both return ``None`` when someone else got there first. That is how replicas agree without
  a lock. ``delete(key, revision=r)`` is conditional the same way.
* **Keys are subject-like**: dotted tokens, and ``items``/``watch`` take NATS wildcards
  (``*`` for one token, ``>`` for the rest).
* **A watch tells you when it has caught up.** ``watch`` first yields every current value,
  then ``None`` once, then live :class:`Change` objects (``value`` is ``None`` for a delete or
  an expiry). Expiry is only visible to watchers on buckets opened with
  ``ttl_markers=True``.
* Watching and listing use short-lived NATS consumers that Micro cleans up for you, so many
  reads leave nothing behind.

Locks
-----

:class:`Locks` are cluster-wide leases with a TTL, built on a table.

.. code-block:: python

   locks = await runtime.locks()
   await locks.gate("identify.0", ttl=5)           # at most one caller per 5 s
   async with locks.hold("nightly-job", ttl=30):   # renewed while held
     ...

* ``try_acquire`` takes a lease if it is free (``None`` otherwise); ``acquire`` waits for it.
* ``gate`` takes a lease and **leaves it to expire**: it spaces out work such as Discord
  identifies, "at most one per ``ttl``".
* ``hold`` keeps the lease renewed (every ``ttl / 3``) while the block runs and releases it
  after. If the lease is taken from you meanwhile (you stalled longer than ``ttl``), the block
  finishes and then :class:`LockLost` is raised, so you know the exclusivity did not hold.

Declarations
------------

A **declaration** is a versioned document that services publish and a consumer applies, with
rollout safety built in. Command sync and the store's schema modules are built on it.

.. code-block:: python

   from micro.coordination import Declarations

   declarations = Declarations(runtime, "commands")
   view = await declarations.view()     # {key: Declared(hash, document, state, live_hashes)}
   await declarations.mark_applied(key, view[key].hash)
   await declarations.forget(key)       # retire a key

A service calls ``service.declare(kind, key, document)``; replicas store the document once,
content-addressed by hash, and advertise ``{key: hash}`` in presence. The consumer asks for
the **converged view**:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - State
     - Meaning
   * - ``converged``
     - Every live declarer agrees on one version: apply it.
   * - ``mixed``
     - Declarers disagree (a rollout is running): the last applied version stands.
   * - ``retained``
     - Nobody declares it right now: the applied version stays until you forget it.

Two versions that appear at once, before anything was applied, wait until they converge. The
result is that a half-finished rollout, or a rollback, never changes what is applied, and a
replica restarting never removes anything.

Reference
---------

.. api::
   micro.coordination.Table
   micro.coordination.Versioned
   micro.coordination.Change
   micro.coordination.Locks
   micro.coordination.LockHolder
   micro.coordination.LockLost
   micro.coordination.Lease
   micro.coordination.Declarations
   micro.coordination.Declared
   micro.coordination.DeclarationState
   micro.coordination.declarations_metadata
   micro.coordination.digest
   micro.coordination.DECLARATIONS_KEY
