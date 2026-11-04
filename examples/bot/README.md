# Example bot

Created with `micro init bot`, then grown in the recommended layout:

- `services/hello.py`: the generated `/hello` with a button.
- `services/greeter.py`: a request service that emits an event.
- `services/audit.py`: event listeners and a durable work queue.
- `services/chat.py`: `!ping`, `/greet` (autocomplete), `/poll start` (buttons),
  `/feedback` (modal), and a "Say hi" user command.
- `services/ticker.py`: a background component.
- `contracts.py`: the schemas services share.

```console
cd examples/bot
DISCORD_TOKEN=... DISCORD_INTENTS=33281 uv run micro up
uv run micro scale app 3
uv run micro roll app
curl -s localhost:8080/requests/example.greet -d '{"name":"Ada"}'
```

`33281` adds the Message Content intent for `!ping`; slash commands need none.
