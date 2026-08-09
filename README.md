# Micro

Micro is an extensible library for building applications from independently
replaceable microservices. Its first major use case is a distributed Discord
bot platform.

Micro currently requires Python 3.14 or newer.

## Service applications

Install the service framework and an ASGI server:

```console
pip install "Micro[service]" uvicorn
```

Declare an event schema and its single handler:

```python
from typing import Annotated

from pydantic import BaseModel, Field

from micro.service import EventSchema, Service

service = Service("hello")


class GreetingPayload(BaseModel):
  name: Annotated[str, Field(min_length=1)]


Greeting = EventSchema[GreetingPayload](
  id="example.greeting",
  payload=GreetingPayload,
)


@service.listen(Greeting)
async def greet(event: GreetingPayload) -> None:
  print(f"Hello, {event.name}!")
```

The service is an ASGI application and can run directly:

```console
uvicorn example:service
```

It can also be mounted inside another ASGI application:

```python
from fastapi import FastAPI

app = FastAPI()
app.mount("/micro", service)
```

`listen()` generates the event endpoint from its schema. Every service also
provides `/schema`, `/health/live`, `/health/ready`, and `/health/drained`.
The schema endpoint accounts for its ASGI mount path without changing the
implementation hash.

Pydantic validates and decodes inbound values. Its generated JSON Schemas remain
the wire format used for discovery and compatibility. For request/response
operations, declare a `RequestSchema[Input, Output]` using input and output
models and register its handler with `@service.handle(...)`.

## Calling services

Every `Service` owns three clients populated by overseer state: `service.client`
for events and typed requests, `service.store` for GraphQL stores, and
`service.gateway` for Gateway control operations. `ServiceClient` routes calls
across every compatible service instance currently known to it. During rolling
updates it compares the advertised operation contract, not only its ID.

```python
payload = GreetingPayload(name="World")
await service.client.emit(Greeting, payload)
reply = await service.client.request(GreetingRequest, payload)
```

`POST /state` atomically replaces the clients' directory snapshot. Snapshots
contain a non-negative revision plus service, store, and Gateway routes; older
revisions are rejected rather than overwriting newer topology.
Identical service schemas are transmitted once in a hash-indexed table, while
each instance route carries only its schema hash.

## Gateway workers

Install the Gateway component with `Micro[gateway]`. `Gateway` is an ASGI
application backed by Hikari's shard/session implementation. Hikari's resource
cache and automatic member chunking are disabled: Micro receives raw dispatch
payloads, while its connection-scoped graph projection will control complete
guild/member ingestion separately.

```python
gateway = Gateway(
  token,
  intents=hikari.Intents.GUILDS | hikari.Intents.GUILD_MESSAGES,
  connection=update_connection_graph,
  shard_ids=[0, 2],
  shard_count=4,
)
```

The overseer pushes queue topology to the gateway before it opens its Discord
connections. Dispatches are published on `gateway.events` as compact
`[event_name, payload]` records. Connection callbacks separately report connect,
disconnect, ready, resume, invalidation, and clean-close transitions. The gateway
starts and closes with ASGI lifespan, so it can run directly under Uvicorn.

Gateway control calls are typed and shard-aware. Guild member requests and voice
state updates route to the worker that owns the guild's shard; presence updates
are broadcast to every Gateway worker:

```python
await service.gateway.request_guild_members(guild_id, query="", limit=0)
await service.gateway.update_voice_state(guild_id, channel_id)
await service.gateway.update_presence(status="idle")
```

`GatewayEventService` instances share one durable queue consumer. The active
instance routes each dispatch once per listening service name and chooses one
replica of that service; implementation hashes do not create duplicate consumer
groups during rolling updates.

Application services listen with the generated builtin schemas and receive the
typed Discord dispatch data (`d`) directly:

```python
from micro.discord.models.gateway import GatewayMessageCreateDispatchData
from micro.schemas import events


@service.listen(events.MESSAGE_CREATE)
async def message_create(event: GatewayMessageCreateDispatchData) -> None: ...
```

## Local graph store

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
