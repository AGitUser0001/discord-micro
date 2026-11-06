# Micro

Discord bots (and other applications) built from independently replaceable
microservices on NATS. One process on a small box, or many machines, with the
same code; scale, roll, or replace any part live.

```console
uv add discord-micro  # or: pip install "discord-micro[all,accel]"
micro init            # adds micro.toml and services/hello/
DISCORD_TOKEN=... micro up
```

```python
# services/hello/__init__.py
from micro.discord.interactions import Commands, Interaction
from micro.service import Service

service = Service("hello")
commands = Commands(service)

@commands.slash("hello", description="Say hello")
async def hello(ctx: Interaction, name: str = "world") -> None:
  await ctx.reply(f"Hello, {name}!")
```

Documentation: `micro docs` (sources in [src/micro/docs](src/micro/docs/index.rst)) (quickstart, services,
Discord, interactions, store, deploying, rolling upgrades, wire reference).
Examples ship with Micro: `micro add example` lists them.
