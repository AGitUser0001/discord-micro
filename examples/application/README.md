# Complete application example

This example runs a small Micro deployment across four independent ASGI
processes and one AGE database:

| Port | Process |
| --- | --- |
| `8100` | Overseer and network-controlled discovery |
| `8101` | Modular GraphQL/GQL store |
| `8102` | Greeting request service |
| `8103` | Audit event service |
| `5455` | Apache AGE |

The application entrypoint loads `example.greetings` into the overseer's store
module catalog. Discovery assigns that module to the store. On reconciliation,
the overseer pushes the complete module document to the store and pushes all
routable service and store locations to the application services.

## Run it

From this directory, start AGE:

```console
docker compose up --build -d age
```

Install the example environment:

```console
uv sync
```

Run these in four terminals:

```console
uv run uvicorn overseer:app --port 8100
uv run uvicorn store:store --port 8101
uv run uvicorn api_service:service --port 8102
uv run uvicorn audit_service:service --port 8103
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

The API service stores the greeting through GraphQL, emits
`example.audit` through `ServiceClient`, and returns the response. The audit
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
