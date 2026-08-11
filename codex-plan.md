# Micro

Micro is an extensible library for building applications from independently replaceable microservices.

Its first major use case is a distributed Discord bot platform that Panel could later use.

Micro has three independent parts:

## `micro.overseer`

`micro.overseer` is the coordinator.

It oversees the complete deployment, including:

- coordinating microservice instances;
- assigning and transferring work;
- monitoring availability;
- handling service startup, shutdown, replacement, and recovery;
- coordinating Gateway workers and shard ownership;
- coordinating Gateway generations and rolling transitions.

It coordinates services without implementing their application logic.

## `micro.gateway`

`micro.gateway` is a Discord Gateway worker.

Each worker:

- maintains Discord WebSocket connections;
- operates the shards currently assigned to it;
- forwards raw Discord payloads to appropriate services;
- executes WebSocket operations through its owned connections;
- changes shard assignments as directed by the overseer;
- participates in recovery and rolling Gateway replacement.

A Gateway worker is not permanently tied to particular shard IDs. If one worker becomes unavailable, another can claim its shards. When it returns, it may be assigned different work.

Gateway generations allow a new collection of workers and connections to start before the old generation is retired. This supports rolling upgrades and shard-count changes.

Guild-scoped WebSocket operations can be routed to the worker owning the guild’s shard.

Global WebSocket control remains an open design problem. Its semantics should be determined later rather than prematurely generalized.

## `micro.service`

`micro.service` is the framework for writing a microservice.

It provides the common integration needed for a service to participate in a Micro deployment, along with reusable **microservice templates**.

A template is an abstraction implemented through functions, classes, decorators, context managers, or similar programming constructs. It packages a particular service-side behavior so individual services do not need to repeatedly implement its mechanics.

Templates may support behaviors involving:

- communication;
- lifecycle;
- work handling;
- concurrency;
- coordination;
- state;
- recovery;
- observability.

The available templates are not a fixed taxonomy. More can be added, and existing templates can be changed, combined, or replaced.

Applications can create any number and kind of microservices with `micro.service`. Discord HTTP handling and application features are examples of services rather than fixed parts of Micro.

## Extensibility

Micro does not prescribe a complete service topology.

- The overseer coordinates the deployment.
- Gateway workers operate Discord Gateway connections.
- The service framework supports arbitrary application microservices.
- Templates provide reusable behavior without restricting what a service can be.
- Applications and extensions can introduce new services and new templates.

Micro should avoid embedding assumptions from Panel or its first deployment into the general service framework.

Its architecture will be refined through implementation rather than completely specified in advance.

Reference:
 - other project: ~/Desktop/Panel

## Implementation checklist

This checklist describes Micro-owned work. It deliberately excludes concerns
that should be supplied by the application host or deployment environment.

### Explicitly out of scope

- [x] Do not implement authentication, authorization, certificate management,
  or secret distribution in Micro. Keep every ASGI application wrappable by
  host-provided middleware.
- [x] Do not implement Kubernetes discovery, deployments, lifecycle control,
  leader election, or Kubernetes API clients. Keep `Discovery`, health,
  readiness, draining, and lifecycle boundaries usable by external adapters.

### Existing foundation

- [x] Provide a shared ASGI microservice lifecycle with schema, live, ready,
  drained, and topology-state endpoints.
- [x] Provide typed service event and request declarations backed by Pydantic.
- [x] Route service events once per logical service and load-balance replicas.
- [x] Push revisioned topology from the overseer and reject stale state.
- [x] Compress identical service schemas into a hash-indexed topology table.
- [x] Compose modular GraphQL schemas and compile supported operations to GQL.
- [x] Provide the Apache AGE development adapter and runnable example.
- [x] Generate Discord HTTP and Gateway models plus builtin event schemas.
- [x] Maintain Discord Gateway connections through Hikari without its cache.
- [x] Publish raw Gateway dispatches through the queue.
- [x] Route guild-specific Gateway control operations by shard ownership.
- [x] Expose queue `publish`, `request`, and `consume` exclusively through the
  queue server; keep JetStream private to the queue backend.
- [x] Support acknowledgement, retry, and request responses on consumed items.
- [x] Run the store, services, overseer, queue, and Gateway event router together
  in `examples/application`.

### 1. Connection-scoped Gateway projection

- [x] Define the graph module for Gateway routing information, connection IDs,
  active state, and connection-owned Discord data.
- [x] Add a projection consumer for every raw Gateway dispatch.
- [x] Store every guild, channel, role, member, emoji, thread, voice state, and
  other enabled-intent object received from Discord.
- [x] Fuse partial create/update/delete dispatches into existing graph objects.
- [x] Begin complete guild/member ingestion after `READY`, including member
  chunk requests where required.
- [x] Mark a connection's projection inactive during a temporary disconnect so
  stale data cannot satisfy cache reads.
- [x] Mark the same projection active again after a successful `RESUMED` event.
- [x] Delete connection-owned projection data after invalidation, clean worker
  shutdown, or overseer-confirmed worker death.
- [x] Ensure replacing one connection cannot delete another connection's data.
- [x] Batch projection writes without delaying application event delivery
  indefinitely.
- [x] Add replay tests proving that dispatch sequences produce deterministic
  graph state.

### 2. Store mutation and execution

- [x] Define directive metadata and compiler behavior for creating entities.
- [x] Define directive metadata and compiler behavior for updating properties
  and relationships.
- [x] Define directive metadata and compiler behavior for deleting entities and
  connection-owned subgraphs.
- [x] Support multi-statement or transactional compiled operations where a
  projection update must be atomic.
- [x] Add batch execution to `GraphExecutor` and the AGE adapter.
- [x] Define indexes and constraints derived from `@entity` keys.
- [x] Define how physical graph layouts evolve when modules change.
- [x] Add pagination and bounded-list compilation.
- [x] Normalize database failures into stable GraphQL errors.
- [x] Test compiler output and execution against real AGE for reads, writes,
  relationships, transactions, and deletion.

### 3. Gateway ownership and recovery

- [x] Represent observed Gateway connections separately from desired shard
  assignments in overseer state.
- [x] Let a Gateway worker report `CONNECTED`, `READY`, `DISCONNECTED`,
  `RESUMED`, `INVALIDATED`, and `CLOSED` transitions to the application-owned
  discovery/control implementation.
- [x] Define assignment state transitions for starting, active, draining, and
  abandoned shards.
- [x] Prevent immediate reassignment after a transient disconnect.
- [x] Allow reassignment after the application host declares a worker dead.
- [x] Ensure only the active connection is used for guild-scoped control calls.
- [x] Define rolling replacement semantics for compatible Gateway workers.
- [x] Define shard-count-change semantics without assuming a particular process
  orchestrator.
- [x] Decide and document global presence semantics across multiple workers.
- [x] Add failure tests for disconnects, invalid sessions, resume failures,
  worker loss, delayed topology, and competing assignments.

Implemented semantics: desired assignments and observed Discord connections are
independent. A disconnect makes the connection and its cache reads inactive but
does not release its assignment; `RESUMED` reactivates the same connection.
Invalidation purges that connection's projection before a fresh `READY` session
is used. Rolling replacement first moves the old assignment to `draining`, then
allows the replacement to become `active`. Presence is one global desired value
broadcast to every worker which currently owns at least one active shard.

Projection lifecycle and data records share one ordered queue channel, while the
raw application-event channel remains metadata-free. Adjacent data records are
coalesced by connection/object identity into one read and one atomic mutation.
AGE layouts evolve additively: stable hashed labels/properties are retained,
new entity labels receive a unique `_micro_id` index, and a topology revision
cannot silently acquire a different physical definition.

### 4. Discord HTTP service template

- [x] Define typed request schemas from the generated Discord OpenAPI models.
- [x] Implement the HTTP worker as a normal Micro service/template.
- [x] Send HTTP work through queue `request` and return the raw/typed response.
- [x] Coordinate Discord rate-limit buckets across HTTP worker replicas.
- [x] Handle global rate limits without centralizing unrelated request work.
- [x] Preserve Discord error bodies, headers, retry timing, and idempotency
  requirements.
- [x] Support multipart uploads without buffering unbounded bodies.
- [x] Add representative endpoints for messages, interactions, commands, and
  guild resources before generating broader conveniences.
- [x] Add deterministic rate-limit and retry tests using a fake Discord server.
- [x] Manage one revisioned Discord credential through Discovery and push it
  only to Gateway and Discord HTTP workers outside standard topology.
- [x] Rotate HTTP authorization live, reconnect managed Gateway workers, reject
  stale credential revisions, and keep rate-limit state stable across rotation.

### 5. Queue semantics and robustness

- [x] Document that delivery is at least once and handlers must tolerate
  redelivery.
- [x] Decide whether Gateway fan-out remains idempotent at-least-once delivery or
  records completion separately for each logical service.
- [x] Add configurable acknowledgement deadlines and delayed retry.
- [x] Add optional dead-letter behavior as backend policy, not payload metadata.
- [x] Add payload and response size limits at the queue server boundary.
- [x] Make request cancellation stop waiting without corrupting the queued item.
- [x] Finish graceful draining for active publish, request, consume, and response
  operations.
- [x] Verify multiple queue-server instances share consumers and can settle
  deliveries received through another instance.
- [x] Add disconnection, redelivery, duplicate response, server restart, and NATS
  partition integration tests.
- [x] Define backend-neutral queue health and capacity observations.

### 6. Overseer and discovery behavior

- [x] Separate desired topology, observed topology, and the last successfully
  distributed topology.
- [x] Expose reconciliation results and per-instance push failures.
- [x] Add periodic or application-triggered reconciliation without assuming how
  discovery obtains instances.
- [x] Define persistence hooks for topology revisions, assignments, and observed
  connection state.
- [x] Recover safely after an overseer restart without reusing revisions.
- [x] Decide whether Micro supports one active overseer or an externally elected
  active overseer; do not implement an orchestration-specific election system.
- [x] Keep Gateway workers alive and connected while the overseer is temporarily
  unavailable.
- [x] Add tests for partial pushes, discovery changes during reconciliation,
  overseer restart, unavailable instances, and recovery.

### 7. Public API and operations

- [x] Replace remaining cross-package private-method use with deliberate shared
  state-application primitives.
- [x] Make timeout, cancellation, retry, and shutdown behavior consistent across
  every client.
- [x] Establish a stable exception hierarchy for routing, remote responses,
  topology, queue settlement, graph compilation, and backend execution.
- [x] Add structured lifecycle and operation events that host applications can
  connect to logging, metrics, and tracing systems.
- [x] Add bounded concurrency and backpressure to every unbounded fan-out or
  processing loop.
- [x] Document every public class, protocol, schema document, and wire endpoint.
- [x] Add package tests that install and import every optional dependency group
  in isolation.
- [x] Add end-to-end tests for the complete example, including clean startup,
  reconciliation, queue delivery, graph access, and graceful shutdown.
- [x] Reassess the public surface before declaring the first stable release;
  remove unused APIs instead of retaining compatibility aliases.
