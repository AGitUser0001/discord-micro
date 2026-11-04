import asyncio
from collections.abc import Mapping
from typing import Any, Protocol
from uuid import uuid7

import hikari

from ._control import GuildMembersRequest, PresenceUpdate, VoiceStateUpdate
from ._events import ConnectionEventKind


class ShardHost(Protocol):
  """What a shard session reports to the worker that owns it."""

  token: str
  intents: hikari.Intents

  async def on_dispatch(
    self, session: ShardSession, name: str, payload: Mapping[str, Any]
  ) -> None: ...

  async def on_connection(
    self, session: ShardSession, kind: ConnectionEventKind
  ) -> None: ...


class ShardSession(Protocol):
  """One Discord Gateway connection for one shard of one generation."""

  generation: int
  shard_id: int
  shard_count: int
  connection_id: str | None

  async def start(self) -> None: ...

  async def close(self) -> None: ...

  async def update_presence(self, update: PresenceUpdate) -> None: ...

  async def request_guild_members(self, request: GuildMembersRequest) -> None: ...

  async def update_voice_state(self, update: VoiceStateUpdate) -> None: ...


class HikariShard:
  """A shard session backed by a cache-free Hikari Gateway bot."""

  def __init__(
    self, host: ShardHost, generation: int, shard_id: int, shard_count: int
  ) -> None:
    self.host = host
    self.generation = generation
    self.shard_id = shard_id
    self.shard_count = shard_count
    self.connection_id: str | None = None
    self.bot: hikari.GatewayBot | None = None
    self._lock = asyncio.Lock()

  async def start(self) -> None:
    async with self._lock:
      if self.bot is not None:
        return
      bot = hikari.GatewayBot(
        self.host.token,
        intents=self.host.intents,
        cache_settings=hikari.impl.CacheSettings(
          components=hikari.api.CacheComponents.NONE
        ),
        auto_chunk_members=False,
        banner=None,
      )
      bot.listen(hikari.ShardPayloadEvent)(self._on_dispatch)
      bot.listen(hikari.ShardConnectedEvent)(self._on_connected)
      bot.listen(hikari.ShardDisconnectedEvent)(self._on_disconnected)
      self.bot = bot
      try:
        await bot.start(
          check_for_updates=False,
          shard_ids=(self.shard_id,),
          shard_count=self.shard_count,
        )
      except BaseException:
        self.bot = None
        raise

  async def close(self) -> None:
    async with self._lock:
      bot, self.bot = self.bot, None
      if bot is not None:
        await bot.close()
      if self.connection_id is not None:
        await self.host.on_connection(self, ConnectionEventKind.CLOSED)
      self.connection_id = None

  async def update_presence(self, update: PresenceUpdate) -> None:
    activity = (
      hikari.Activity(
        name=update.activity.name,
        type=hikari.ActivityType(update.activity.type),
        url=update.activity.url,
        state=update.activity.state,
      )
      if update.activity is not None
      else None
    )
    await self._bot().update_presence(
      status=hikari.Status(update.status),
      idle_since=update.idle_since,
      activity=activity,
      afk=update.afk,
    )

  async def request_guild_members(self, request: GuildMembersRequest) -> None:
    kwargs: dict[str, Any] = {
      "include_presences": request.include_presences,
      "limit": request.limit,
    }
    if request.query is not None:
      kwargs["query"] = request.query
    if request.users is not None:
      kwargs["users"] = request.users
    if request.nonce is not None:
      kwargs["nonce"] = request.nonce
    await self._bot().request_guild_members(request.guild_id, **kwargs)

  async def update_voice_state(self, update: VoiceStateUpdate) -> None:
    await self._bot().update_voice_state(
      update.guild_id,
      update.channel_id,
      self_mute=update.self_mute,
      self_deaf=update.self_deaf,
    )

  def _bot(self) -> hikari.GatewayBot:
    if self.bot is None:
      raise RuntimeError("Shard session is not connected.")
    return self.bot

  async def _on_dispatch(self, event: hikari.ShardPayloadEvent) -> None:
    if event.name == "READY":
      if self.connection_id is not None:
        await self.host.on_connection(self, ConnectionEventKind.INVALIDATED)
      self.connection_id = str(uuid7())
      await self.host.on_connection(self, ConnectionEventKind.READY)
      await self._request_initial_members(event.payload)
    elif event.name == "RESUMED":
      await self.host.on_connection(self, ConnectionEventKind.RESUMED)
    await self.host.on_dispatch(self, event.name, event.payload)

  async def _on_connected(self, event: hikari.ShardConnectedEvent) -> None:
    await self.host.on_connection(self, ConnectionEventKind.CONNECTED)

  async def _on_disconnected(self, event: hikari.ShardDisconnectedEvent) -> None:
    await self.host.on_connection(self, ConnectionEventKind.DISCONNECTED)

  async def _request_initial_members(self, payload: Mapping[str, Any]) -> None:
    if not self.host.intents & hikari.Intents.GUILD_MEMBERS or self.bot is None:
      return
    guilds = payload.get("guilds")
    if not isinstance(guilds, list):
      return
    for guild in guilds:
      if not isinstance(guild, Mapping):
        continue
      guild_id = guild.get("id")
      if isinstance(guild_id, str) and guild_id.isdecimal():
        await self.bot.request_guild_members(
          int(guild_id),
          include_presences=bool(self.host.intents & hikari.Intents.GUILD_PRESENCES),
          query="",
          limit=0,
          nonce=f"micro:{guild_id}",
        )
