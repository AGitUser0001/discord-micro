# Apache AGE store example

This importable example package keeps all database-specific implementation
outside `micro.store`.
It translates Micro's canonical GQL into AGE-compatible Cypher and executes it
through an async Psycopg connection pool.

Other examples can depend on the local `micro-age` distribution and use
`from micro_age import ApacheAgeExecutor`.

Start AGE from the repository root:

```console
docker compose -f examples/apache_age/compose.yaml up --build -d age
```

Run the store service with the HTTP bridge (NATS must be running, for example
`nats-server -js`):

```console
cd examples/apache_age
uv run micro run store:store micro.http:HTTPBridge
```

Create and retrieve a vertex through the store's `micro.store.execute` request:

```console
curl -sS http://127.0.0.1:8080/requests/micro.store.execute \
  -d '{"query":"mutation { createPerson(name: \"Ada\") { name } }"}'

curl -sS http://127.0.0.1:8080/requests/micro.store.execute \
  -d '{"query":"{ person(name: \"Ada\") { name } }"}'
```

Set `MICRO_AGE_URL` to replace the default local connection URL.
