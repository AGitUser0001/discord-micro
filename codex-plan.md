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

- [ ] Do not implement authentication, authorization, certificate management,
  or secret distribution in Micro. Keep every ASGI application wrappable by
  host-provided middleware.
- [ ] Do not implement Kubernetes discovery, deployments, lifecycle control,
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

- [ ] Define the graph module for Gateway routing information, connection IDs,
  active state, and connection-owned Discord data.
- [ ] Add a projection consumer for every raw Gateway dispatch.
- [ ] Store every guild, channel, role, member, emoji, thread, voice state, and
  other enabled-intent object received from Discord.
- [ ] Fuse partial create/update/delete dispatches into existing graph objects.
- [ ] Begin complete guild/member ingestion after `READY`, including member
  chunk requests where required.
- [ ] Mark a connection's projection inactive during a temporary disconnect so
  stale data cannot satisfy cache reads.
- [ ] Mark the same projection active again after a successful `RESUMED` event.
- [ ] Delete connection-owned projection data after invalidation, clean worker
  shutdown, or overseer-confirmed worker death.
- [ ] Ensure replacing one connection cannot delete another connection's data.
- [ ] Batch projection writes without delaying application event delivery
  indefinitely.
- [ ] Add replay tests proving that dispatch sequences produce deterministic
  graph state.

### 2. Store mutation and execution

- [ ] Define directive metadata and compiler behavior for creating entities.
- [ ] Define directive metadata and compiler behavior for updating properties
  and relationships.
- [ ] Define directive metadata and compiler behavior for deleting entities and
  connection-owned subgraphs.
- [ ] Support multi-statement or transactional compiled operations where a
  projection update must be atomic.
- [ ] Add batch execution to `GraphExecutor` and the AGE adapter.
- [ ] Define indexes and constraints derived from `@entity` keys.
- [ ] Define how physical graph layouts evolve when modules change.
- [ ] Add pagination and bounded-list compilation.
- [ ] Normalize database failures into stable GraphQL errors.
- [ ] Test compiler output and execution against real AGE for reads, writes,
  relationships, transactions, and deletion.

### 3. Gateway ownership and recovery

- [ ] Represent observed Gateway connections separately from desired shard
  assignments in overseer state.
- [ ] Let a Gateway worker report `CONNECTED`, `READY`, `DISCONNECTED`,
  `RESUMED`, `INVALIDATED`, and `CLOSED` transitions to the application-owned
  discovery/control implementation.
- [ ] Define assignment state transitions for starting, active, draining, and
  abandoned shards.
- [ ] Prevent immediate reassignment after a transient disconnect.
- [ ] Allow reassignment after the application host declares a worker dead.
- [ ] Ensure only the active connection is used for guild-scoped control calls.
- [ ] Define rolling replacement semantics for compatible Gateway workers.
- [ ] Define shard-count-change semantics without assuming a particular process
  orchestrator.
- [ ] Decide and document global presence semantics across multiple workers.
- [ ] Add failure tests for disconnects, invalid sessions, resume failures,
  worker loss, delayed topology, and competing assignments.

### 4. Discord HTTP service template

- [ ] Define typed request schemas from the generated Discord OpenAPI models.
- [ ] Implement the HTTP worker as a normal Micro service/template.
- [ ] Send HTTP work through queue `request` and return the raw/typed response.
- [ ] Coordinate Discord rate-limit buckets across HTTP worker replicas.
- [ ] Handle global rate limits without centralizing unrelated request work.
- [ ] Preserve Discord error bodies, headers, retry timing, and idempotency
  requirements.
- [ ] Support multipart uploads without buffering unbounded bodies.
- [ ] Add representative endpoints for messages, interactions, commands, and
  guild resources before generating broader conveniences.
- [ ] Add deterministic rate-limit and retry tests using a fake Discord server.

### 5. Queue semantics and robustness

- [ ] Document that delivery is at least once and handlers must tolerate
  redelivery.
- [ ] Decide whether Gateway fan-out remains idempotent at-least-once delivery or
  records completion separately for each logical service.
- [ ] Add configurable acknowledgement deadlines and delayed retry.
- [ ] Add optional dead-letter behavior as backend policy, not payload metadata.
- [ ] Add payload and response size limits at the queue server boundary.
- [ ] Make request cancellation stop waiting without corrupting the queued item.
- [ ] Finish graceful draining for active publish, request, consume, and response
  operations.
- [ ] Verify multiple queue-server instances share consumers and can settle
  deliveries received through another instance.
- [ ] Add disconnection, redelivery, duplicate response, server restart, and NATS
  partition integration tests.
- [ ] Define backend-neutral queue health and capacity observations.

### 6. Overseer and discovery behavior

- [ ] Separate desired topology, observed topology, and the last successfully
  distributed topology.
- [ ] Expose reconciliation results and per-instance push failures.
- [ ] Add periodic or application-triggered reconciliation without assuming how
  discovery obtains instances.
- [ ] Define persistence hooks for topology revisions, assignments, and observed
  connection state.
- [ ] Recover safely after an overseer restart without reusing revisions.
- [ ] Decide whether Micro supports one active overseer or an externally elected
  active overseer; do not implement an orchestration-specific election system.
- [ ] Keep Gateway workers alive and connected while the overseer is temporarily
  unavailable.
- [ ] Add tests for partial pushes, discovery changes during reconciliation,
  overseer restart, unavailable instances, and recovery.

### 7. Public API and operations

- [ ] Replace remaining cross-package private-method use with deliberate shared
  state-application primitives.
- [ ] Make timeout, cancellation, retry, and shutdown behavior consistent across
  every client.
- [ ] Establish a stable exception hierarchy for routing, remote responses,
  topology, queue settlement, graph compilation, and backend execution.
- [ ] Add structured lifecycle and operation events that host applications can
  connect to logging, metrics, and tracing systems.
- [ ] Add bounded concurrency and backpressure to every unbounded fan-out or
  processing loop.
- [ ] Document every public class, protocol, schema document, and wire endpoint.
- [ ] Add package tests that install and import every optional dependency group
  in isolation.
- [ ] Add end-to-end tests for the complete example, including clean startup,
  reconciliation, queue delivery, graph access, and graceful shutdown.
- [ ] Reassess the public surface before declaring the first stable release;
  remove unused APIs instead of retaining compatibility aliases.
