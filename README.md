# Micro

Discord bots (and other applications) built from independently replaceable
microservices on NATS. One process on a small box, or many machines, with the
same code; scale, roll, or replace any part live.

```console
uvx --from micro micro init mybot
cd mybot
DISCORD_TOKEN=... uv run micro up
```

```python
# src/mybot/services/hello.py
from micro.discord.interactions import Commands, Interaction
from micro.service import Service

service = Service("hello")
commands = Commands(service)

@commands.slash("hello", description="Say hello")
async def hello(ctx: Interaction, name: str = "world") -> None:
  await ctx.reply(f"Hello, {name}!")
```

Documentation: [docs/index.rst](docs/index.rst) (quickstart, services,
Discord, interactions, store, deploying, rolling upgrades, wire reference).
Example: [examples/bot](examples/bot/README.md).
