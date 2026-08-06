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
from micro.service import EventSchema, EventScope, Service

service = Service("hello")

Greeting = EventSchema[dict](
  id="example.greeting",
  scope=EventScope.keyed("name"),
  payload={
    "type": "object",
    "properties": {"name": {"type": "string", "minLength": 1}},
    "required": ["name"],
    "additionalProperties": False,
  },
)


@service.listen(Greeting)
async def greet(event: dict) -> None:
  print(f"Hello, {event['name']}!")
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

For request/response operations, declare a `RequestSchema[Input, Output]` and
register its handler with `@service.handle(...)`. Unlike an event listener,
the handler's returned JSON is checked against the declared output schema and
returned with a `200 OK` response.

## Calling services

`ServiceClient` routes calls across every compatible instance currently known to
it. Registrations can be supplied initially, added or removed individually, or
replaced atomically from an overseer state snapshot. During rolling updates it
compares the advertised operation contract, not only its ID.

```python
from micro.client import ServiceClient

client = ServiceClient()
client.add("hello-1", "http://127.0.0.1:8001", service_schema)

await client.emit(Greeting, {"name": "World"})
reply = await client.request(GreetingRequest, {"name": "World"})
```

A service configured with `Service(..., state_receiver=client)` accepts complete
directory snapshots at `POST /state`. Snapshots contain a non-negative
`revision` and an `instances` list; older revisions are rejected rather than
overwriting newer topology.
