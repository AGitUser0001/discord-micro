# Complete application example

This example runs a small Micro deployment across six independent ASGI
processes and the reusable AGE and JetStream adapters:

| Port | Process |
| --- | --- |
| `8100` | Overseer and network-controlled discovery |
| `8101` | Modular GraphQL/GQL store |
| `8102` | Greeting request service |
| `8103` | Audit event service |
| `8104` | NATS-backed queue ingress |
| `8105` | Gateway-event queue consumer and router |
| `5455` | Apache AGE |
| `4222` | NATS JetStream |

The application entrypoint loads `example.greetings` into the overseer's store
module catalog. Discovery assigns that module to the store. On reconciliation,
the overseer pushes the complete module document to the store and pushes all
routable service and store locations to the application services.

## Run it

From this directory, start AGE and NATS. The AGE service builds the Docker context
from `../apache_age`:

```console
docker compose up --build -d age nats
```

Install the example environment. Its local `micro-age` dependency also
comes from `../apache_age`, so the application does not duplicate the executor:

```console
uv sync
```

Run these in six terminals:

```console
uv run uvicorn overseer:app --port 8100
uv run uvicorn store:store --port 8101
uv run uvicorn api_service:service --port 8102
uv run uvicorn audit_service:service --port 8103
uv run uvicorn queue_service:queue --port 8104
uv run uvicorn gateway_event_service:event_service --port 8105
```

Once every process is ready, register the routes and push topology revision `0`:

```console
uv run configure.py
```

Call the greeting service through its standard request endpoint:

```console
curl -sS http://127.0.0.1:8102/requests/example.greet \
  -H 'Content-Type: application/json' \
  -d '{"name":"World"}'
```

The API service looks up a greeting through `service.store`, emits
`example.audit` through `service.client`, and returns the response. The audit
worker prints the event.

The stored graph data can also be queried directly:

```console
curl -sS http://127.0.0.1:8101/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ greeting(name: \"World\") { name message } }"}'
```

`NetworkDiscovery` is deliberately only a control-plane building block. Put
authentication or a trusted-network boundary around `/discovery` and `/refresh`
in a real deployment.
