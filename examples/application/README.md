# Example bot

`app.py` defines a few components: a `greeter` request service, an `audit`
service (event listener plus a durable work queue), a Discord `bot` service with
`Commands`, `Components`, and `Modals` templates (`/greet` with autocomplete,
`/poll start` with vote buttons, `/feedback` with a modal, a "Say hi" user
command, and `!ping`), and a `ticker` background component. The configs also run
the builtin `InteractionRouter` and `CommandSync` templates.

## One process

```console
cd examples/application
export DISCORD_TOKEN=...
uv run micro up
```

`micro up` starts `nats-server -js` on `127.0.0.1:4222` if nothing is listening
(store in `.micro/nats`) and runs `micro.toml`'s single process. The HTTP bridge
listens on `127.0.0.1:8080`:

```console
curl -s localhost:8080/requests/example.greet -d '{"name":"Ada"}'
curl -s localhost:8080/components
```

## Many processes

```console
uv run micro up micro.multi.toml
uv run micro ps
uv run micro scale greeter 3
uv run micro roll bot
uv run micro gateway shards 2
uv run micro commands list
```

Same code, different config. Two Gateway workers split the shards, two HTTP
workers split the rate-limit buckets, and every group can be scaled or rolled
while the bot stays online.
