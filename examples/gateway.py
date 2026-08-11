import os

import hikari

from micro.gateway import ConnectionEvent, Gateway


async def connection(event: ConnectionEvent) -> None:
  print(event.kind, event.shard_id, event.connection_id)


gateway = Gateway(
  os.environ["DISCORD_TOKEN"],
  intents=hikari.Intents.GUILDS | hikari.Intents.GUILD_MESSAGES,
  connection=connection,
  shard_count=1,
)
