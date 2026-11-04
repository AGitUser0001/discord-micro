# Micro operations and wire contracts

Micro assumes a trusted NATS network. It does not implement authentication,
secret distribution, or orchestration; secure NATS with its own accounts/TLS and
supply the Discord token through the host environment. Every name below is
defined once in `micro/subjects.py`.

## Runtime and lifecycle

A `Runtime` owns one NATS connection and JetStream context per process and hosts
components. On start it ensures the `MICRO_EVENTS` stream and the presence
bucket. Components move through `created → starting → running → draining →
closed`: draining stops taking new work, finishes in-flight work, and releases
leases. `Runtime.serve` (used by `micro run`) drains on the first SIGINT/SIGTERM
and closes immediately on a second.

`MICRO_NATS_URL` (comma separated) selects servers; the default is
`nats://127.0.0.1:4222`. `Runtime(replicas=3)` creates streams and buckets with
R3 replication for a three-node cluster.

## Presence

Bucket `micro_presence`, key `<kind>.<id>`, value `Registration`
(`kind`, `name`, `instance`, `id`, `metadata`). Entries are written with a per-key
TTL (`presence_ttl`, default 10 s) and renewed every third of it; expiry markers
make crashed components disappear from every `Directory` watcher. Kinds:

| Kind | Metadata |
| --- | --- |
| `service` | `version`, `requests` (id → schema hash), `events`, `work`, `modules` |
| `gateway` | `max_concurrency`; the id is the worker's lease owner |
| `discord.http` | the id is the worker's routing address |
| `http` | `url` |
| `runtime` | `pid`, `host`, `components` (written by `micro run`) |

## Requests

`micro.req.<request_id>`, queue group `<request_id>`. Headers: `Micro-Schema`
(caller's input/output hash) on requests; `Micro-Status: ok|error` on replies.
Error bodies are `{"code", "message", "detail"}`. Framework codes:
`invalid_input`, `invalid_output`, `incompatible_schema`, `handler_failed`; any
other code comes from a handler's `ServiceError`. No responders becomes
`RoutingError`. Draining a replica drains its subscription, so requests already
delivered still complete and new ones go to other replicas.

## Events and dispatches

Stream `MICRO_EVENTS` (interest retention: a message is kept until every
consumer interested in it acknowledges it; events without listeners are
dropped):

| Subject | Publisher |
| --- | --- |
| `micro.evt.<event_id>` | `Client.emit` |
| `micro.discord.dispatch.<EVENT>.<guild_id or _>` | the shard owner in the active generation |
| `micro.discord.standby.<EVENT>.<guild_id or _>` | every other connection (for the projection) |
| `micro.gateway.connection.<shard_id>` | `ConnectionEvent` lifecycle records |

Dispatch bodies are Discord's raw `d` payload with headers `Micro-Shard`,
`Micro-Generation`, and `Micro-Connection`.

Each service with listeners has one durable pull consumer `svc_<name>` filtered
to its listened subjects (guild filters become subject filters). Replicas share
it. Delivery is **at least once**: an event is acknowledged after every matching
handler succeeds; if any fails, it is redelivered to the service with backoff
and every matching handler runs again, so handlers must be idempotent. A payload
that does not match its schema is terminated. Long handlers send progress acks,
so there is no handler deadline.

## Work queues

`WorkQueue("name", Model)` uses stream `MICRO_WORK_<NAME>` (work-queue retention)
on `micro.work.<name>` with one durable consumer `work_<name>`. Jobs are kept
until exactly one worker acknowledges them.

## Discord HTTP

Workers subscribe to `micro.discord.http.<id>` (no queue group). The client
computes a partition key (Discord's major parameters: channel, guild, webhook,
interaction token; otherwise the operation ID) and sends to the highest
rendezvous-hash worker in presence, falling back down the ranking if a worker
just left. Every request sharing a rate-limit bucket therefore reaches one
worker, whose buckets live in memory. A global 429 is broadcast on
`micro.ratelimit.discord.global` as `{"until": <unix time>}`. Bodies are
`DiscordHTTPRequest`/`DiscordHTTPResponse` JSON (bytes as base64).

## Gateway

| Store | Key | Value |
| --- | --- | --- |
| `micro_gateway` | `generation.desired` | `GatewayGeneration` (`id`, `shard_count`) |
| `micro_gateway` | `generation.active` | the generation whose owners publish |
| `micro_gateway` | `presence` | `PresenceUpdate` applied to every connection |
| `micro_shards` | `<generation>.<shard_id>` | `ShardLease` (`owner`, `ready`, `releasing`, `connection_id`), TTL `lease_ttl` |
| `micro_locks` | `identify.<shard_id % max_concurrency>` | 5 s gate before each identify |

Each worker runs both the desired and active generations. It claims free shards
up to `ceil(shard_count / workers)`, marks one shard `releasing` when it is over
its share while a peer is under, and opens a standby connection for a releasing
shard; once that connection is READY it starts publishing and then takes the
lease, so a handoff overlaps rather than gaps. Expired leases are reclaimed.
Draining marks every lease releasing and waits until peers have taken them over
(or no peers remain). When every shard of the desired generation is leased and
READY, any worker compare-and-sets `generation.active`, and the old generation's
connections close.

The active owner of a shard subscribes to `micro.gateway.ctl.<shard_id>.members`
and `.voice` (queue group `micro.gateway`) for `GuildMembersRequest` and
`VoiceStateUpdate`. Presence is the `presence` key, not a message.

## Store (optional)

`Store` is a service answering `micro.store.execute` (`GraphQLBody` →
`{"data", "errors"}`). It composes the union of graph modules declared by live
services (`Service.uses`) plus its own, and recomposes when presence changes.
`GatewayProjection` is an optional service consuming dispatch, standby, and
connection subjects in order; run one replica.

## Supervisor

`micro up` subscribes to `micro.supervisor.<deployment>.scale|roll|ps` with JSON
bodies (`{"process", "replicas"}`, `{"process"}`, `{}`) and replies
`{"ok", "processes" | "error"}`. Rolling starts a replacement, waits for its
`runtime` presence entry, then SIGTERMs (drains) the old process.
