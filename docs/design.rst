Design decisions
================

* **NATS is the substrate.** Discovery, request/reply, durable delivery,
  leases, and coordination state; no coordinator process.
* **Templates over frameworks.** Builtins (router, commands, components,
  modals, sync, HTTP bridge) are ordinary services and extensions built on
  public pieces; replace or subclass any of them.
* **Requests route by ID**, not service name, so a request can move between
  services.
* **Discovery is presence** (TTL KV, watched); routing truth comes from NATS
  (consumers, queue groups).
* **Rendezvous-hashed HTTP partitions** keep each rate-limit bucket on one
  worker with in-memory state.
* **Interactions are queue items with a deadline**: per-route work-queue
  consumers shared by every replica and version, a 3 s TTL, at-most-once.
* **Declarations converge** across rollouts; nothing applies half-deployed.
* **Compatibility by validation**, forward-compatible records.
* **Lazy imports**: generated models split per definition.
* Out of scope: authentication, secret distribution, orchestration, voice
  audio, a discord.py shim, an in-process cache.
