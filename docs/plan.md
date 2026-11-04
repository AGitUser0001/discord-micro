# Micro rewrite: NATS-native, overseer-free

Micro is a scalable, live-updatable Discord bot platform built from independently
replaceable microservices. The first implementation got the hard parts right
(typed models, Gateway generations, shard handoff, cluster-wide rate limits) but
was centralized around an overseer, made the store mandatory infrastructure,
and had no unified runtime. This plan makes NATS the substrate, removes the
overseer, and then builds the Discord application layer on top. Panel should
eventually run on it.

Names in this plan illustrate requirements; the developer API is the product
and is designed to be small, typed, and pleasant. `codex-plan.md` records the
previous design.

## Decisions (section 0)

- **NATS is a hard core dependency** (`nats-py`), reversing "keep JetStream
  private to the queue backend". Applications still never touch JetStream
  directly: `micro.service`, `micro.queue`, and `micro.coordination` abstract it.
- **Discovery is the presence bucket**, not the NATS Services (`$SRV`) protocol:
  one deterministic, watch-driven mechanism (per-key TTLs with expiry markers)
  that Gateway and HTTP workers need anyway. `$SRV` compatibility can be added
  later without changing the API.
- **Requests route by request ID** (`micro.req.<id>`, queue group `<id>`), not by
  service name, so a request can move between services without callers changing.
  Ownership conflicts are reported from presence.
- **Discord HTTP partitioning is rendezvous hashing** over live HTTP workers in
  presence, keyed by Discord's major parameters, so every request sharing a
  bucket reaches one worker and only the departed worker's partitions move.
- **Token rotation is a rolling restart** with the new environment value; the
  token is never stored in NATS.
- **`micro.queue` becomes typed durable work queues** over JetStream
  (`WorkQueue`, `Service.work`, `Client.enqueue`) instead of being deleted.
- **HTTP survives only as a template component**: `micro.http.HTTPBridge`
  serves probes, discovery, request/event forwarding, and Gateway admin, and is
  meant to be subclassed. Everything internal is NATS.
- **Easy launching without an orchestrator**: `micro run` hosts components in one
  process; `micro up micro.toml` supervises a whole deployment on one machine
  (starts `nats-server` if needed, replicas, restarts, `scale`, `roll`, `ps`).
  The same components run unchanged under systemd, Docker, k3s, or MicroK8s.

## Target architecture

1. **NATS (substrate)**: discovery, request/reply, load balancing, durable event
   delivery, leases, small coordination state. Single node for development and
   the Jetson; a 3-node R3 cluster or leaf nodes for redundancy.
2. **Micro (developer experience)**: the per-process runtime, the typed service
   framework, Gateway workers, Discord HTTP workers, and the Discord application
   layer.
3. **Store (optional application storage)**: an ordinary service.

Design rules:

- [x] Every builtin runs with zero store (`tests/test_deployment.py`, and
  `tests/test_package_surface.py` checks builtins never import the store).
- [x] No component is required for others to keep working, except NATS.
- [x] Deployment shape is configuration, not code.
- [x] Prefer partitioning over shared state; share state only through NATS KV.
- [x] No authentication, secret distribution, or Kubernetes integration in Micro.

Subjects, streams, and buckets: see `docs/operations.md` and `micro/subjects.py`.

## Checklist

### 1. Runtime and launcher

- [x] Per-process runtime owning one NATS connection, one JetStream context, and
  shared tables; per-client HTTP pools and `apply_state_atomically` deleted.
- [x] One component lifecycle: start, ready, drain, close.
- [x] `micro run module:component ...` and a `micro.toml` deployment file.
- [x] SIGTERM drains then closes; a second signal closes immediately.
- [x] HTTP probes through the `HTTPBridge` template.
- [x] `micro up` supervisor with `ps`, `scale`, and `roll`.

### 2. Service framework on NATS

- [x] `Service`, `EventSchema`, `RequestSchema`, `@handle`, `@listen`, typed payloads.
- [x] Requests via queue groups; typed `RemoteError` codes and `ServiceError`.
- [x] Events via one durable consumer per logical service.
- [x] Presence registration with version, schema hashes, events, work, modules.
- [x] Rolling updates by starting new replicas and draining old ones; schema
  hashes checked at request time.

### 3. Gateway workers without an overseer

- [x] Presence with TTL renewal.
- [x] Self-balancing shard leases with compare-and-set, reclaiming expired leases
  and releasing over-share shards gracefully (gap-free handoff).
- [x] Identify concurrency gates in `micro_locks`.
- [x] Only the publishing owner publishes dispatches.
- [x] Generations in `micro_gateway`; new generation connects, then flips.
- [x] Guild control subjects owned by the lease holder; presence as one KV value.
- [x] `micro gateway status|shards|roll|presence`.

### 4. Discord HTTP workers

- [x] In-memory buckets in partitioned workers; store rate limits deleted.
- [x] Global limit: per-worker detection plus a broadcast to every worker.
- [x] Generated `DiscordHTTPClient` methods kept; transport is NATS.

### 5. Store as an optional service

- [x] Services declare modules; the store composes the ones in presence.
- [x] Store queries/mutations are an ordinary request (`micro.store.execute`).
- [x] Compiler, composer, directives, and AGE executor unchanged.
- [x] Gateway projection is an optional service.

### 6. Delete

- [x] `micro.overseer`, `GatewayEventService`, HTTP event routing, per-client
  transports, `StoreRateLimits`, the old queue server and NATS backend example.
- [x] `pyproject.toml` extras and `tests/test_package_surface.py` updated.

### 7. Tests, examples, docs

- [x] Tests against an ephemeral `nats-server -js` (`nats_url` fixture).
- [x] Behavior tests ported: routing, assignment, rolling generations, rate
  limits, projection.
- [x] Failure tests: crashed Gateway worker reclaimed, replica drained mid-load
  without losing requests, HTTP partitions move when workers leave.
- [x] Zero-store deployment test.
- [x] `examples/application`: one-process and multi-process configs.
- [x] `docs/operations.md` rewritten.
- [x] Pyright at zero errors.

## Discord application layer (next)

Out of scope: a discord.py compatibility shim, voice audio, a second in-process
cache.

### 8. Event dispatch and routing

- [x] Any number of handlers per event in one service, one delivery per service.
- [x] `when=` predicates and `guild_id=` filters pushed into consumer subjects.
- [ ] Discord-specific filter helpers (ignore bots, ignore self, channel).
- [x] Handler failures isolated and logged with event and handler.
- [x] Delivery guarantee: at least once; any failure redelivers the event.
- [ ] Re-run only failed handlers on redelivery, if it proves worth the state.
- [ ] Optional per-guild ordering, with its cost documented.
- [x] Typed payloads from the generated schemas.

### 9. Interaction routing

- [ ] Route each interaction to one owning service by command path, component or
  modal `custom_id` prefix, or autocomplete option (a subject per route).
- [ ] Ownership declared in presence; conflicts reported.
- [ ] Automatic deferral before Discord's 3-second deadline; latency measured.
- [ ] Unroutable interactions get an ephemeral error.

### 10. Interaction responses

- [ ] Initial response, defer, follow-up, edit/delete original, modal,
  autocomplete, component updates; through HTTP workers keyed by token.
- [ ] Token lifetime (15 minutes) enforced with a clear error.
- [ ] A typed `custom_id` codec within 100 characters (learning from Panel's).

### 11. Command declaration and sync

- [ ] Typed slash, user, and message commands.
- [ ] Bulk overwrite sync skipped when the stored definition hash is unchanged.
- [ ] One sync per change, coordinated through `micro_locks`.

### 12. Reading Discord state

- [ ] Typed reads of guilds, channels, members, roles, permissions.
- [x] A disconnected projection never serves stale data (kept from before).
- [ ] HTTP fallback when the projection cannot answer, visible to the caller.

### 13. Ergonomics

- [ ] Short helpers for replies, embeds, safe `allowed_mentions`, components.

### 14. Example bot

- [x] Message listener, request, event, work queue, and background task, in one
  process or many from the same code.
- [ ] Slash command, button, and modal (needs sections 9–11).

## Afterwards

Port Panel onto Micro.
