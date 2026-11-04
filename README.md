# Micro

Discord bots (and other applications) built from independently replaceable
microservices on NATS. One process on a small box, or many machines, with the
same code; scale, roll, or replace any part live.

```python
from micro.discord.interactions import Commands, Interaction
from micro.service import Service

bot = Service("hello")
commands = Commands(bot)

@commands.slash("hello", description="Say hello")
async def hello(ctx: Interaction, name: str = "world") -> None:
  await ctx.reply(f"Hello, {name}!")
```

```console
pip install "Micro[gateway,http,accel]"
DISCORD_TOKEN=... micro up
```

Documentation: [docs/index.rst](docs/index.rst) (quickstart, services,
Discord, interactions, store, deploying, rolling upgrades, wire reference).
Example: [examples/application](examples/application/README.md).
