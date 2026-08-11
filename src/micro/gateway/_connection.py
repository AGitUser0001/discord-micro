import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Any, Protocol
from uuid import uuid7

import hikari

from ._events import ConnectionEvent, ConnectionEventKind, Dispatch


class _GatewayBot(Protocol):
  def listen[EventT: hikari.Event](
    self, *event_types: type[EventT]
  ) -> Callable[
    [Callable[[EventT], Awaitable[None]]], Callable[[EventT], Awaitable[None]]
  ]: ...

  async def start(
    self,
    *,
    check_for_updates: bool = True,
    shard_ids: Sequence[int] | None = None,
    shard_count: int | None = None,
  ) -> None: ...

  async def close(self) -> None: ...
  async def join(self) -> None: ...
  async def update_presence(self, **kwargs: Any) -> None: ...
  async def request_guild_members(self, guild: int, **kwargs: Any) -> None: ...
  async def update_voice_state(
    self, guild: int, channel: int | None, **kwargs: Any
  ) -> None: ...


class ShardOwner(Protocol):
  intents: hikari.Intents

  @property
  def credential(self) -> str: ...

  def create_bot(self) -> _GatewayBot: ...

  async def publish_dispatch(
    self, dispatch: Dispatch, *, application: bool
  ) -> None: ...

  async def report_connection(self, event: ConnectionEvent) -> None: ...


class ShardConnection:
  """One independently replaceable Discord shard connection."""

  def __init__(self, gateway: ShardOwner, shard_id: int, shard_count: int) -> None:
    self.gateway = gateway
    self.shard_id = shard_id
    self.shard_count = shard_count
    self.bot: _GatewayBot | None = None
    self.started = False
    self.connection_id: str | None = None
    self.may_publish = False
    self._lock = asyncio.Lock()

  async def identify(self) -> None:
    async with self._lock:
      if self.started:
        return
      bot = self.prepare()
      self.started = True
      try:
        await bot.start(
          check_for_updates=False,
          shard_ids=(self.shard_id,),
          shard_count=self.shard_count,
        )
      except BaseException:
        self.started = False
        self.bot = None
        raise

  def prepare(self) -> _GatewayBot:
    if self.bot is None:
      self.bot = self.gateway.create_bot()
      self._subscribe(self.bot)
    return self.bot

  async def stop(self) -> None:
    async with self._lock:
      bot, self.bot = self.bot, None
      was_started, self.started = self.started, False
      if bot is not None and was_started:
        await bot.close()
      if self.connection_id is not None:
        await self.gateway.report_connection(
          ConnectionEvent(ConnectionEventKind.CLOSED, self.shard_id, self.connection_id)
        )
      self.connection_id = None

  async def join(self) -> None:
    if self.bot is not None:
      await self.bot.join()

  def _subscribe(self, bot: _GatewayBot) -> None:
    bot.listen(hikari.ShardPayloadEvent)(self._on_dispatch)
    bot.listen(hikari.ShardConnectedEvent)(self._on_connected)
    bot.listen(hikari.ShardDisconnectedEvent)(self._on_disconnected)

  async def _on_dispatch(self, event: hikari.ShardPayloadEvent) -> None:
    if event.name == "READY":
      if self.connection_id is not None:
        await self.gateway.report_connection(
          ConnectionEvent(
            ConnectionEventKind.INVALIDATED, self.shard_id, self.connection_id
          )
        )
      self.connection_id = str(uuid7())
      await self.gateway.report_connection(
        ConnectionEvent(ConnectionEventKind.READY, self.shard_id, self.connection_id)
      )
      await self._request_initial_members(event.payload)
    elif event.name == "RESUMED":
      await self.gateway.report_connection(
        ConnectionEvent(ConnectionEventKind.RESUMED, self.shard_id, self.connection_id)
      )
    await self.gateway.publish_dispatch(
      Dispatch(event.name, event.payload, self.shard_id, self.connection_id),
      application=self.may_publish,
    )

  async def _on_connected(self, event: hikari.ShardConnectedEvent) -> None:
    await self.gateway.report_connection(
      ConnectionEvent(ConnectionEventKind.CONNECTED, self.shard_id, self.connection_id)
    )

  async def _on_disconnected(self, event: hikari.ShardDisconnectedEvent) -> None:
    await self.gateway.report_connection(
      ConnectionEvent(
        ConnectionEventKind.DISCONNECTED, self.shard_id, self.connection_id
      )
    )

  async def _request_initial_members(self, payload: Mapping[str, Any]) -> None:
    if not self.gateway.intents & hikari.Intents.GUILD_MEMBERS:
      return
    guilds = payload.get("guilds")
    if not isinstance(guilds, list) or self.bot is None:
      return
    for guild in guilds:
      if not isinstance(guild, Mapping):
        continue
      guild_id = guild.get("id")
      if isinstance(guild_id, str) and guild_id.isdecimal():
        await self.bot.request_guild_members(
          int(guild_id),
          include_presences=bool(self.gateway.intents & hikari.Intents.GUILD_PRESENCES),
          query="",
          limit=0,
          nonce=f"micro:{self.connection_id}:{guild_id}",
        )
