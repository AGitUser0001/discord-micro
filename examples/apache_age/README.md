# Apache AGE store example

This example keeps all database-specific implementation outside `micro.store`.
It translates Micro's canonical GQL into AGE-compatible Cypher and executes it
through an async Psycopg connection pool.

Start AGE from the repository root:

```console
docker compose -f examples/apache_age/compose.yaml up --build -d age
```

Run the GraphQL store:

```console
cd examples/apache_age
uv run uvicorn store:store --port 8000
```

Create and retrieve a vertex through GraphQL:

```console
curl -sS http://127.0.0.1:8000/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"mutation { createPerson(name: \"Ada\") { name } }"}'

curl -sS http://127.0.0.1:8000/graphql \
  -H 'Content-Type: application/json' \
  -d '{"query":"{ person(name: \"Ada\") { name } }"}'
```

Set `MICRO_AGE_URL` to replace the default local connection URL.
