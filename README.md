# Micro

Discord bots (and other applications) built from independently replaceable
microservices on NATS. One process on a small box, or many machines, with the
same code; scale, roll, or replace any part live.

```console
uv add micro          # or: pip install "micro[all,accel]"
micro init            # adds micro.toml and services/hello.py
DISCORD_TOKEN=... micro up
```

```python
# services/hello.py
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
