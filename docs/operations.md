# Micro operations and wire contracts

Micro assumes a trusted application network. It deliberately does not implement
authentication, certificate management, Kubernetes integration, or leader
election. Deployments may run one overseer, or select one active overseer using
an external lease and pass its result through `is_active`.

## Standard worker endpoints

Every `Microservice` exposes `GET /schema`, `/health/live`, `/health/ready`, and
`/health/drained`, plus `POST /state` when it consumes topology. Shutdown first
stops accepting new work and then waits for tracked operations. Hosts can attach
structured lifecycle observers with `add_observer`.
Operations expose matching started/completed/failed records through
`add_operation_observer`; adapters can forward both event types to their own
logging, metrics, or tracing system.

## Queue

Queue delivery is **at least once**. Consumers must make handlers idempotent.
Gateway fan-out deliberately uses idempotent at-least-once delivery, with one
settlement per logical service rather than a global completion record.

`POST /channels/{channel}` publishes bytes. `POST
/channels/{channel}/request` publishes and waits for a response. `POST
/channels/{channel}/consumers/{consumer}` obtains a delivery capability. The
`/deliveries/acknowledge`, `/retry`, `/respond`, and `/dead_letter` endpoints
settle it; retry accepts a `delay` in seconds. `GET /queue/observations` exposes
backend-neutral connection, backlog, consumer, and active-operation values.
Payload and response limits are enforced while reading ASGI body chunks.

## Discord HTTP

Discord's OpenAPI `operationId` values define the queue protocol. Generation
produces typed body, query, and response fragments in `models.http`, then
defragments them into concrete request and response contracts in
`models.http_requests`. Every response-body union is a Pydantic `RootModel`,
not a type alias. A physical `DiscordHTTPClient` method and `HTTP_OPERATIONS`
registry entry are generated for every operation. For example,
`create_message` accepts `CreateMessageHTTPRequest`; callers never supply an
HTTP path or method.

`DiscordHTTPClient` carries the operation ID and validated input data through
the `discord.http` queue channel. `DiscordHTTPWorker` expands path, query, and
header parameters, selects the declared JSON, form, or multipart body encoding,
and returns status, duplicate-preserving headers, and body without translating
Discord errors. Binary multipart fields use base64 on the JSON queue wire and
are restored before HTTP encoding. Queue payload limits bound the complete
request. Rate-limit coordinators track route buckets and the global limit
independently; share or externally implement the coordinator when workers live
in separate processes.

## Overseer

The overseer tracks desired discovery state, observed Gateway connections, and
the revision last distributed to each instance separately. A revision is
persisted before network pushes, so a failed attempt is never reused after a
restart. Partial push results remain visible through `GET /topology` and
`last_reconciliation`. Periodic reconciliation is optional. Workers retain
their last topology and continue running while the overseer is unavailable.
