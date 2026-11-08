Configuration
=============

:class:`Config` is a **typed settings document shared by every process** in a deployment.
It is one Pydantic model stored in a NATS key-value bucket (``micro_config``), so there is no
config server and nothing to broadcast: each process watches the key and moves its own
snapshot to every new revision.

.. code-block:: python

   from pydantic import BaseModel, ConfigDict

   class Limits(BaseModel):
     model_config = ConfigDict(frozen=True, extra="ignore")
     rate: int = 10
     burst: int = 3

   limits = await runtime.config("limits", Limits)    # opens, creates if missing, starts

   limits.value.rate                    # this process's snapshot, a plain attribute read
   await limits.update(rate=20)         # every process follows
   async for change in limits.watch():  # or react to changes
     print(change.old.rate, "->", change.new.rate)

``runtime.config(...)`` returns a started :class:`Config` that closes with the runtime.
Make the model ``frozen`` (the snapshot is shared, not copied) and ``extra="ignore"`` so a
newer or older version of the model can read the same document during a rollout.

Bootstrap settings
------------------

Settings needed to *reach* NATS (the address, credentials) and secrets such as the Discord
token cannot come from NATS, so they stay in each process's environment. For the rest,
``bootstrap`` is this process's own idea of the settings:

.. code-block:: python

   limits = Config(runtime, "limits", Limits, bootstrap=Limits(rate=int(os.environ.get("RATE", 10))))
   limits.value        # the bootstrap value, available immediately, before anything connects
   await limits.start()
   limits.value        # now the shared document

* Before ``start`` (or while NATS is unreachable), ``value`` is the bootstrap value and
  ``loaded`` is false.
* If no document exists yet, the bootstrap value is written as the initial document. This is
  **atomic**: processes starting at the same moment create one document, and all of them read
  it back, so everyone starts from the same revision. Pass ``seed=False`` to require that
  something else created it (``ConfigMissing`` otherwise).
* After that **the stored document wins**; a process's bootstrap never overwrites it.

Reading and writing
-------------------

* ``config.value`` and ``config.revision`` are the local snapshot. ``await config.read()`` is
  the stored document and revision right now.
* ``await config.update(rate=20)`` or ``update(lambda c: c.model_copy(update={...}))`` changes
  the document **safely**: it reads the stored document, applies your change, and writes only
  if nothing intervened, retrying on conflict. Concurrent updates from any number of processes
  are never lost. The function may run more than once, so keep it free of side effects. A change
  that results in the same document writes nothing.
* ``await config.set(value, revision=r)`` replaces the document **only if it is still at
  revision** ``r``, else raises :class:`ConfigConflict`: write back what you read without a lost
  update. Without ``revision`` it overwrites (the way to repair an invalid document).
* A value that does not validate is refused before anything is written.
* ``await config.wait_for(revision)`` waits until this process's snapshot reaches a revision
  (a write returns before the watch has delivered it back). It raises :class:`ConfigRejected` if
  that revision is rejected, and :class:`ConfigClosed` if the config closes.

Refresh middleware
------------------

Before the snapshot is replaced, the incoming document runs through a chain of async
middleware that sees the old and the new configuration. It is where side effects belong:
validate beyond the model, prepare something, call a service.

.. code-block:: python

   @limits.use
   async def check(refresh, next):
     if refresh.new.burst > refresh.new.rate:
       raise refresh.reject("burst cannot exceed rate")      # dropped for good
     if refresh.changed.get("rate") and not downstream_ready():
       raise refresh.defer(5)                                # hold back, try again in 5 s
     await resize_pool(refresh.old.rate, refresh.new.rate)   # a side effect
     await next()                                          # continue: the change applies

A middleware receives a :class:`Refresh` with ``old``, ``new``, ``revision``, ``previous``
(the revision of ``old``), ``attempt`` (counts retries), ``initial`` (true for the first
document this process loads, replacing the bootstrap value) and ``changed`` (``{field: (old,
new)}``). It nests like all Micro middleware (:doc:`middleware`), the first added outermost,
and ends in one of four ways:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - It does
     - What happens
   * - ``await next()`` and returns
     - The whole chain finished, so the snapshot is replaced (``on_change`` listeners and
       ``watch()`` then fire).
   * - ``raise refresh.reject("why")``
     - This revision is dropped and **never retried**. The old snapshot stays, the issue is
       reported, and a later revision is handled normally.
   * - ``raise refresh.defer(delay)``
     - The old snapshot stays and the revision is **held**: retried after ``delay`` seconds, or
       (no delay) on the next change or ``config.retry()``. A newer revision supersedes it.
   * - raises anything else
     - The old snapshot stays, the error is reported, and the revision is retried with a
       growing backoff (1, 2, 4 ... 60 seconds), against whatever the latest revision is by then.

Because a failed refresh is retried, **side effects must be idempotent**, and since the snapshot
is replaced only after the entire chain returns, a failure in an outer layer after an inner one
did its work also retries the whole chain. Calling ``end()`` instead of ``next()`` counts as a
deferral.

Errors and issues
~~~~~~~~~~~~~~~~~

``config.on_error(listener)`` is called with a :class:`ConfigIssue` (``kind``, ``revision``,
``error``) for each ``rejected``, ``deferred``, ``failed``, ``invalid`` (a stored value that does
not validate: the snapshot is kept and the next valid revision recovers) and ``watch`` problem,
and ``config.last_error`` keeps the latest. They are also logged.

Staying in sync
---------------

The watch starts at the same time the document is loaded, so a change made in between is not
lost. If the connection drops, nothing needs doing: the watch resumes where it was, and if it
has to be rebuilt the process re-reads the stored document and catches up. A deleted document
is reported and the snapshot is kept. ``close()`` (done by the runtime) cancels the tasks and
ends every ``watch()`` and ``wait_for``.

The Gateway's table
-------------------

Gateway workers read the ``gateway`` table and follow it: shard count, intents, identify
concurrency, lease TTL and presence all live there, so they are changed in one place with no
worker argument or environment variable to disagree. See :doc:`gateway` for the fields and how
each takes effect. Programmatically:

.. code-block:: python

   control = GatewayControl(runtime)
   await control.configure(intents="unprivileged,message_content", shard_count=2)
   await control.update_presence(status="idle")

Terminal editor: ``micro configure``
------------------------------------

``micro configure`` is a full-screen editor for **every table** in the shared configuration.

.. code-block:: console

   micro configure             # all tables
   micro configure gateway     # open one directly

* **Left:** the tables. **Right:** the selected table's fields, with their types. Move with the
  arrow keys (or ``j``/``k``), ``enter`` opens a table or changes a field, ``←`` goes back.
* **Changing a field** depends on its type: booleans toggle, fixed choices (a status, an enum)
  cycle, objects open so you can edit their fields (an unset optional object is created with its
  defaults), and anything else opens a prompt; the first key you type replaces the current value,
  and the value is read as JSON when it is JSON (``20``, ``true``), else as text.
* **Safe by construction.** A write is applied to the latest stored revision and refused rather
  than overwritten if someone changed the table meanwhile (it re-applies your edit to the newer
  document). When the table's model is known, a value the model refuses (``lease_ttl`` below 3)
  is shown as an error and nothing is written.
* **Live.** Changes other processes make appear as they happen.
* ``d`` sets a field to null, ``a`` / ``x`` add and remove keys (in tables without a model, or
  fields that are dictionaries), ``e`` edits the whole table as JSON in ``$VISUAL``/``$EDITOR``,
  ``c`` creates a table that does not exist yet from its model's defaults, ``r`` reloads, ``q``
  quits.
* **Which tables.** All tables stored in NATS appear. Models for validation and defaults come from
  the Gateway's own settings, and from the ``[config]`` table of ``micro.toml``:

  .. code-block:: toml

     [config]
     limits = "myapp.config:Limits"      # name = "module:Model"

  A table without a known model can still be edited; it just is not validated here (the processes
  that use it still reject an invalid value in their own refresh).
* Without a terminal (a pipe, CI) it prints the tables read-only instead.

Reference
---------

.. api::
   micro.config.Config
   micro.config.Refresh
   micro.config.Applied
   micro.config.ConfigIssue
   micro.config.ConfigError
   micro.config.ConfigRejected
   micro.config.ConfigDeferred
   micro.config.ConfigConflict
   micro.config.ConfigMissing
   micro.config.ConfigInvalid
   micro.config.ConfigClosed
   micro.gateway.GatewaySettings
   micro.subjects.CONFIG_BUCKET
