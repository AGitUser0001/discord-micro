Rolling upgrades
================

Old and new versions run side by side during every rollout (``micro dev roll``,
or starting new processes and stopping old ones). Micro treats that as normal.

What converges
--------------

Command definitions and graph modules apply a new version only when **every
live replica declaring it agrees**. Mid-rollout the applied version stands; a
rollback changes nothing; stopping every replica removes nothing (retire with
``micro commands forget``).

Compatibility rules
-------------------

* **Requests** are compatible if the input validates against the handler's
  model; schema hashes only explain failures (``incompatible_schema``).
  Add fields as optional.
* **Events and jobs** that a replica cannot decode are left for another
  replica while the service runs mixed schema versions, and rejected once all
  replicas agree.
* **Commands**: options a handler doesn't know are ignored; new options should
  be optional. A required option Discord didn't send yet replies "updated,
  try again" instead of crashing.
* **Custom IDs**: append optional state fields; new prefix for breaking changes.
* **Micro's records** (leases, presence, generations, wire messages) ignore
  unknown fields, so a newer Micro's data never breaks an older one.

Infrastructure
--------------

* Gateway: shard handoff overlaps (duplicates, never gaps); ``micro gateway
  roll`` or ``shards N`` builds a new generation before it publishes.
* HTTP workers: only a departed worker's partitions move.
* Services: draining finishes in-flight requests; queue groups route new ones
  to remaining replicas.
