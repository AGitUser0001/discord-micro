import asyncio
from collections.abc import Mapping
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Protocol
from uuid import uuid7

if TYPE_CHECKING:
  import hikari

from ._control import GuildMembersRequest, PresenceUpdate, VoiceStateUpdate
from ._events import ConnectionEventKind


class ShardHost(Protocol):
  """What a shard session reports to the worker that owns it."""

  token: str
  api_url: str | None

  def intents_for(self, generation: int) -> hikari.Intents:
    """The intents a generation's connections use."""
    ...

  async def on_dispatch(
    self, session: ShardSession, name: str, payload: Mapping[str, Any]
  ) -> None:
    """Called by a shard session with every dispatch it receives."""
    ...

  async def on_connection(
    self, session: ShardSession, kind: ConnectionEventKind
  ) -> None:
    """Called by a shard session when its connection state changes."""
    ...


class ShardSession(Protocol):
  """One Discord Gateway connection for one shard of one generation."""

  generation: int
  shard_id: int
  shard_count: int
  connection_id: str | None

  async def start(self) -> None:
    """Connect this shard."""
    ...

  async def close(self) -> None:
    """Disconnect this shard."""
    ...

  async def update_presence(self, update: PresenceUpdate) -> None:
    """Set the bot's presence on this shard."""
    ...

  async def request_guild_members(self, request: GuildMembersRequest) -> None:
    """Ask Discord for a guild's members on this shard."""
    ...

  async def update_voice_state(self, update: VoiceStateUpdate) -> None:
    """Join, move or leave a voice channel on this shard."""
    ...


class HikariShard:
  """A shard session backed by a Hikari Gateway bot with no cache of its own."""

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
    self._chunked: set[str] = set()

  async def start(self) -> None:
    """Start a hikari bot with no cache of its own for this shard."""
    import hikari

    async with self._lock:
      if self.bot is not None:
        return
      bot = hikari.GatewayBot(
        self.host.token,
        intents=self.host.intents_for(self.generation),
        cache_settings=hikari.impl.CacheSettings(
          components=hikari.api.CacheComponents.NONE
        ),
        auto_chunk_members=False,
        banner=None,
        rest_url=self.host.api_url,
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
        # A start that fails or is cancelled halfway has already opened hikari's REST
        # session; closing the bot is what releases it. Shielded so a cancel still closes it.
        with suppress(Exception):
          await asyncio.shield(bot.close())
        raise

  async def close(self) -> None:
    """Close the hikari bot."""
    async with self._lock:
      bot, self.bot = self.bot, None
      if bot is not None:
        await bot.close()
      if self.connection_id is not None:
        await self.host.on_connection(self, ConnectionEventKind.CLOSED)
      self.connection_id = None

  async def update_presence(self, update: PresenceUpdate) -> None:
    """Set the bot's presence through hikari."""
    import hikari

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
    """Send a request-guild-members command through hikari."""
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
    """Send a voice-state update through hikari."""
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

  # hikari's `listen` calls inspect.signature on these, which evaluates their
  # annotations on Python 3.14. hikari is imported inside `start` (importing
  # micro.gateway must not require it), so the event types stay quoted;
  # ruff's UP037 would unquote them and bring back a NameError.
  async def _on_dispatch(self, event: "hikari.ShardPayloadEvent") -> None:  # noqa: UP037
    if event.name == "READY":
      self._chunked = set()  # before any await: GUILD_CREATEs are handled alongside
      if self.connection_id is not None:
        await self.host.on_connection(self, ConnectionEventKind.INVALIDATED)
      self.connection_id = str(uuid7())
      await self.host.on_connection(self, ConnectionEventKind.READY)
      await self._request_initial_members(event.shard, event.payload)
    elif event.name == "RESUMED":
      await self.host.on_connection(self, ConnectionEventKind.RESUMED)
    elif event.name == "GUILD_DELETE":
      # An outage or a removal: if the guild comes back, its member list is asked for again.
      self._chunked.discard(str(event.payload.get("id")))
    elif event.name == "GUILD_CREATE":
      # A guild joined after READY is never in READY's list.
      await self._request_members(event.shard, event.payload.get("id"))
    await self.host.on_dispatch(self, event.name, event.payload)

  async def _on_connected(self, event: "hikari.ShardConnectedEvent") -> None:  # noqa: UP037
    await self.host.on_connection(self, ConnectionEventKind.CONNECTED)

  async def _on_disconnected(self, event: "hikari.ShardDisconnectedEvent") -> None:  # noqa: UP037
    await self.host.on_connection(self, ConnectionEventKind.DISCONNECTED)

  async def _request_initial_members(
    self,
    shard: hikari.api.GatewayShard,
    payload: Mapping[str, Any],
  ) -> None:
    guilds = payload.get("guilds")
    for guild in guilds if isinstance(guilds, list) else ():
      if isinstance(guild, Mapping):
        await self._request_members(shard, guild.get("id"))

  async def _request_members(
    self,
    shard: hikari.api.GatewayShard,
    guild_id: object,
  ) -> None:
    """Ask Discord for every member of a guild once per connection, so the
    aggregated state holds every member and no lookup needs a rate-limited REST call."""
    import hikari

    if (
      not self.host.intents_for(self.generation) & hikari.Intents.GUILD_MEMBERS
      or not isinstance(guild_id, str)
      or not guild_id.isdecimal()
      or guild_id in self._chunked
    ):
      return
    self._chunked.add(guild_id)
    # The shard itself: the bot's shard count is not known yet during READY.
    await shard.request_guild_members(
      int(guild_id),
      include_presences=bool(
        self.host.intents_for(self.generation) & hikari.Intents.GUILD_PRESENCES
      ),
      query="",
      limit=0,
      nonce=f"micro:{guild_id}",
    )
