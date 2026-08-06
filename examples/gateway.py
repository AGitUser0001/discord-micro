import os

import hikari

from micro.gateway import ConnectionEvent, Dispatch, Gateway


async def dispatch(event: Dispatch) -> None:
  print(event.name, event.shard_id, event.sequence, event.payload)


async def connection(event: ConnectionEvent) -> None:
  print(event.kind, event.shard_id, event.connection_id)


gateway = Gateway(
  os.environ["DISCORD_TOKEN"],
  intents=hikari.Intents.GUILDS | hikari.Intents.GUILD_MESSAGES,
  dispatch=dispatch,
  connection=connection,
)
