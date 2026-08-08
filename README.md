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

`ServiceClient` routes calls across every compatible instance currently known to
it. Registrations can be supplied initially, added or removed individually, or
replaced atomically from an overseer state snapshot. During rolling updates it
compares the advertised operation contract, not only its ID.

```python
from micro.client import ServiceClient

client = ServiceClient()
client.add("hello-1", "http://127.0.0.1:8001", service_schema)

payload = GreetingPayload(name="World")
await client.emit(Greeting, payload)
reply = await client.request(GreetingRequest, payload)
```

A service configured with `Service(..., state_receiver=client)` accepts complete
directory snapshots at `POST /state`. Snapshots contain a non-negative
`revision` and an `instances` list; older revisions are rejected rather than
overwriting newer topology.

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
  dispatch=forward_dispatch,
  connection=update_connection_graph,
  shard_ids=[0, 2],
  shard_count=4,
)
```

The dispatch callback receives the event name, shard ID, connection ID, a local
per-connection sequence, and Hikari's raw payload. Connection callbacks report
connect, disconnect, ready, resume, invalidation, and clean-close transitions.
The gateway starts and closes with ASGI lifespan, so it can run directly under
Uvicorn.

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
