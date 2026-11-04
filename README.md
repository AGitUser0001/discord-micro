# Micro

Micro is a library for building Discord bots (and other applications) from
independently replaceable microservices. One process on a small box runs the
whole thing; the same code spreads over many processes and machines with only a
config change, and any part can be scaled, rolled, or replaced live.

**NATS is the only required infrastructure.** Discovery, request/reply, load
balancing, durable events, leases, and coordination state all live in NATS
(JetStream). There is no coordinator process: every component keeps working as
long as NATS is up. Micro requires Python 3.14 or newer.

- [docs/operations.md](docs/operations.md): subjects, streams, buckets, CLI.
- [docs/plan.md](docs/plan.md): the architecture plan, its decisions, and progress.
- [examples/application](examples/application/README.md): a runnable bot.

## Install

```console
pip install "Micro[gateway,http,accel]"
```

The core needs only NATS (`nats-py`), Pydantic, and HTTPX. Extras: `gateway`
(Hikari), `store` (GraphQL store), `http` (Starlette/Uvicorn bridge), `accel`
(uvloop/winloop). You need a `nats-server` binary; `micro up` starts one for you.

## Services

```python
from pydantic import BaseModel

from micro.service import EventSchema, RequestSchema, Service, ServiceError


class Greeting(BaseModel):
  name: str


class Reply(BaseModel):
  message: str


GREET = RequestSchema[Greeting, Reply](id="example.greet", input=Greeting, output=Reply)
GREETED = EventSchema[Greeting](id="example.greeted", payload=Greeting)

service = Service("greeter")


@service.handle(GREET)
async def greet(request: Greeting) -> Reply:
  if not request.name:
    raise ServiceError("empty_name", "Say who to greet.")
  await service.client.emit(GREETED, request)
  return Reply(message=f"Hello, {request.name}!")


@service.listen(GREETED)
async def log(event: Greeting) -> None:
  print("greeted", event.name)
```

- **Requests** (`@service.handle`): exactly one replica answers; replicas
  load-balance through a NATS queue group. Callers get typed results or a
  `RemoteError` carrying the handler's `ServiceError` code. Input/output schema
  hashes are compared on every call, so a mismatched rolling update fails loudly.
- **Events** (`@service.listen`): every listening *service* gets each event once,
  load-balanced across its replicas, through one durable JetStream consumer.
  A service may have any number of handlers per event, with `when=` predicates
  and (for Discord dispatches) `guild_id=` filters pushed down to NATS. Delivery
  is at least once; a failing handler is logged and the event is redelivered.
- **Work** (`@service.work(queue)`): `WorkQueue` jobs are kept until exactly one
  worker finishes them, even if no worker is running yet.
- `service.uses(module)` declares graph modules an optional store must serve.

Call from anywhere with `Client(runtime)` (or `service.client`):
`request`, `emit`, `enqueue`.

## Running it

A **runtime** is one process's NATS connection; it hosts any number of
**components** (services, Gateway workers, HTTP workers, the HTTP bridge, your
own `Component` subclasses). Each has a `start → drain → close` lifecycle and
SIGTERM drains before closing, so replacing a process is "start the new one, stop
the old one".

```console
micro run example:service micro.discord:DiscordHTTPWorker   # one process
micro up                                                    # micro.toml
```

`micro.toml` describes a whole deployment:

```toml
name = "bot"
nats = "nats://127.0.0.1:4222"

[processes.gateway]
components = ["micro.gateway:GatewayWorker"]

[processes.app]
components = ["app:greeter", "app:bot", "micro.discord:DiscordHTTPWorker"]
replicas = 2
```

`micro up` starts a local `nats-server -js` if none is reachable, runs every
process group, restarts crashes, and drains everything on Ctrl-C. While it runs:

```console
micro ps                  # processes and live components
micro scale app 4         # change replicas
micro roll app            # start new replicas, wait until ready, drain old ones
micro gateway status      # shard leases and generations
micro gateway shards 4    # roll in a generation with 4 shards
micro gateway presence idle --activity "maintenance"
```

Because components never know how they were launched, the same objects also run
under systemd, Docker, or Kubernetes, one component per container or all in one.

## Discord

- `GatewayWorker` (extra `gateway`) keeps Hikari Gateway connections without a
  cache. Workers balance shards among themselves through TTL leases, reclaim a
  crashed worker's shards, hand shards over without gaps when draining, respect
  identify concurrency, and roll new generations (shard count changes) in beside
  the active one before flipping publishing. Only the owner of a shard publishes
  its dispatches.
- `DiscordHTTPWorker` executes the generated Discord API operations with
  in-memory rate-limit buckets. `DiscordHTTPClient(runtime)` routes each call by
  rendezvous hashing over live workers so every request sharing a bucket reaches
  the same worker; global limits are broadcast to all workers.
- `GatewayControl(runtime)` requests guild members, updates voice state, sets the
  global presence, and manages generations.
- Listen to dispatches with the generated schemas in `micro.schemas.events`:

```python
from micro.discord.models.gateway import GatewayMessageCreateDispatchData
from micro.schemas import events


@service.listen(events.MESSAGE_CREATE, guild_id=1234)
async def message_create(event: GatewayMessageCreateDispatchData) -> None: ...
```

The Discord token comes from the host (`DISCORD_TOKEN`); Micro never stores it
in NATS. Rotate it by rolling the processes with the new environment.

## HTTP bridge

`micro.http.HTTPBridge` (extra `http`) is a template component: health probes,
`/components`, `POST /requests/{id}`, `POST /events/{id}`, and Gateway admin
routes. Subclass it or add routes to `bridge.app`. Put it behind your own auth.

## Optional graph store

The local development database is PostgreSQL with Apache AGE. Start it with:

```console
docker compose -f examples/apache_age/compose.yaml up --build -d age
```

The development defaults are:

- host: `127.0.0.1`
- port: `5455`
- database: `micro`
- user: `micro`
- password: `micro`
- graph: `micro`

Set `MICRO_AGE_PORT` or `MICRO_AGE_PASSWORD` before starting Compose to override
the exposed port or password. Existing database volumes retain the credentials
with which they were initialized.

AGE clients must load the extension and select its catalog on every connection:

```sql
LOAD 'age';
SET search_path = ag_catalog, "$user", public;
```

Store APIs are composed from Micro graph modules. Entity identity comes from
`@entity`; root lookups explicitly map their arguments with the runtime Python
macro `@from`:

```graphql
type Guild @entity(key: ["id"]) {
  id: ID!
  name: String!
}

type Query {
  guild(id: ID!): Guild @from(key: "{'id': id}")
}
```

Micro compiles operations over the composed schema into canonical ISO GQL.
Physical labels, properties, and reference types use deterministic hashes of
their schema coordinates. Entities reset the storage path and can therefore be
shared wherever the composed graph references them.

`@entity` and `@from` are ordinary registered directive metadata. Composition
attaches typed metadata to the annotated type or field; the universal compiler
then uses that metadata while planning each request. Applications can install
additional field and type directives through the `directives` and
`type_directives` arguments accepted by both `Store` and `Overseer`.

The universal compiler handles multiple root fields, aliases, variables,
named and inline fragments, `@skip` and `@include`, `__typename`, nested field
arguments backed by directives, object and scalar results, and query, mutation,
or subscription operation roots. Storage behavior is never inferred: every
root field and every argument-sensitive nested field must attach a registered
runtime directive.
