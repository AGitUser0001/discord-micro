![Banner for Micro](./banner.png)

# Micro

Discord bots (and other applications) built from independently replaceable
microservices on NATS. One process on a small box, or many machines, with the
same code; scale, roll, or replace any part live.

```console
uv add discord-micro  # or: pip install "discord-micro[all,accel]"
micro init            # adds micro.toml and services/hello/
DISCORD_TOKEN=... micro dev
```

```python
# services/hello/__init__.py
from micro.discord.interactions import Commands, Interaction
from micro.service import Service

service = Service("hello")
commands = Commands(service)


@commands.slash("hello", description="Say hello")
async def hello(ctx: Interaction, name: str = "world") -> None:
  await ctx.respond(f"Hello, {name}!")
```

Documentation: `micro docs` (sources in [src/micro/docs](src/micro/docs/index.rst)) (quickstart, services,
Discord, interactions, store, deploying, rolling upgrades, wire reference).
Examples are packages fetched from a git source (needs git): `micro pkg list` shows them, `micro pkg add builtin/chat` copies one in, and `micro pkg upgrade` merges newer versions into your edited copy, leaving conflict markers where you both changed the same lines.

Development: `uv run python scripts/smoke.py` runs the whole stack (NATS, the
Gateway through hikari's real websocket, interactions, command sync) against a
fake Discord, `scripts/fake_discord.py`, in about half a minute.

Chat and EverythingBogo was here.

Msmastr74 was also here
