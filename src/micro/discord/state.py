"""Typed reads of Discord state: the projection when it can answer, else HTTP."""

import asyncio
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from micro.discord.objects import Channel, Guild, Member, Role
from micro.errors import MicroError

if TYPE_CHECKING:
  from micro.discord import DiscordHTTPClient
  from micro.runtime import Runtime

logger = logging.getLogger("micro")

ADMINISTRATOR = 1 << 3
ALL_PERMISSIONS = (1 << 53) - 1
"""Every permission bit Discord can define (JSON-safe integer range)."""

type Source = Literal["projection", "http"]


@dataclass(frozen=True, slots=True)
class StateRead[T]:
  """A value and where it came from; `http` means the projection could not answer."""

  value: T
  source: Source


class DiscordState:
  """Reads guilds, channels, members, roles, and computed permissions.

  The Gateway projection answers when a store and projection are running and
  the guild's connection is live (a disconnected connection never serves
  stale data); otherwise reads fall back to the Discord HTTP API.
  """

  def __init__(self, runtime: Runtime, http: DiscordHTTPClient | None = None) -> None:
    from micro.discord import DiscordHTTPClient

    self.runtime = runtime
    self.http = http or DiscordHTTPClient(runtime)
    self._fetching: dict[tuple[str, str], asyncio.Future[Any]] = {}

  async def guild(self, guild_id: int | str) -> StateRead[Guild]:
    projected = await self._projected(guild_id, "guild", str(guild_id))
    if projected is not None:
      return StateRead(Guild.model_validate(projected), "projection")
    guild = await self.http.call("get_guild", path={"guild_id": str(guild_id)})
    return StateRead(Guild.model_validate(guild), "http")

  async def roles(self, guild_id: int | str) -> StateRead[list[Role]]:
    projected = await self._projected(guild_id, "guild", str(guild_id))
    if projected is not None and isinstance(projected.get("roles"), list):
      return StateRead(
        [Role.model_validate(r) for r in projected["roles"]], "projection"
      )
    roles = await self.http.call("list_guild_roles", path={"guild_id": str(guild_id)})
    return StateRead([Role.model_validate(role) for role in roles], "http")

  async def channel(
    self, channel_id: int | str, *, guild_id: int | str | None = None
  ) -> StateRead[Channel]:
    if guild_id is not None:
      projected = await self._projected(guild_id, "channel", str(channel_id))
      if projected is not None:
        return StateRead(
          Channel.model_validate({"guild_id": str(guild_id), **projected}), "projection"
        )
    channel = await self.http.call("get_channel", path={"channel_id": str(channel_id)})
    return StateRead(Channel.model_validate(channel), "http")

  async def member(self, guild_id: int | str, user_id: int | str) -> StateRead[Member]:
    projected = await self._projected(guild_id, "member", f"{guild_id}:{user_id}")
    if projected is not None:
      return StateRead(Member.model_validate(projected), "projection")
    key = (str(guild_id), str(user_id))
    pending = self._fetching.get(key)
    if pending is None:
      # Concurrent lookups of one member share a single REST call.
      pending = asyncio.ensure_future(
        self.http.call(
          "get_guild_member",
          path={"guild_id": key[0], "user_id": key[1]},
        )
      )
      self._fetching[key] = pending
      pending.add_done_callback(lambda _: self._fetching.pop(key, None))
    return StateRead(Member.model_validate(await asyncio.shield(pending)), "http")

  async def permissions(
    self,
    guild_id: int | str,
    user_id: int | str,
    channel_id: int | str | None = None,
  ) -> StateRead[int]:
    """A member's effective permission bits, in a channel if given."""
    guild = await self.guild(guild_id)
    member = await self.member(guild_id, user_id)
    roles = (
      guild.value.roles if guild.value.roles else (await self.roles(guild_id)).value
    )
    sources = {guild.source, member.source}
    channel = None
    if channel_id is not None:
      read = await self.channel(channel_id, guild_id=guild_id)
      sources.add(read.source)
      channel = read.value
    value = compute_permissions(
      str(guild_id), guild.value.owner_id, roles, member.value, str(user_id), channel
    )
    return StateRead(value, "http" if "http" in sources else "projection")

  async def _projected(
    self, guild_id: int | str, kind: str, object_id: str
  ) -> dict[str, Any] | None:
    from micro.gateway import GatewayControl
    from micro.store import StoreClient

    try:
      connection = await GatewayControl(self.runtime).connection_for(int(guild_id))
      if connection is None:
        return None
      result = await StoreClient(self.runtime).execute(
        """
        query Read($connection: ID!, $kind: String!, $id: ID!) {
          object: discordObject(connectionId: $connection, kind: $kind, id: $id) { payload }
        }
        """,
        variables={"connection": connection, "kind": kind, "id": object_id},
      )
    except MicroError, ImportError:
      return None
    data = result.get("data") or {}
    found = data.get("object") if isinstance(data, dict) else None
    payload = found.get("payload") if isinstance(found, dict) else None
    return payload if isinstance(payload, dict) else None


def compute_permissions(
  guild_id: str,
  owner_id: str | None,
  roles: list[Role],
  member: Member,
  user_id: str,
  channel: Channel | None = None,
) -> int:
  """Discord's permission algorithm: roles, administrator, then overwrites."""
  if owner_id is not None and owner_id == user_id:
    return ALL_PERMISSIONS
  by_id = {role.id: role for role in roles}
  base = int(by_id[guild_id].permissions) if guild_id in by_id else 0
  for role_id in member.roles:
    if role_id in by_id:
      base |= int(by_id[role_id].permissions)
  if base & ADMINISTRATOR:
    return ALL_PERMISSIONS
  if channel is None:
    return base
  overwrites = {item.id: item for item in channel.permission_overwrites}
  value = base
  everyone = overwrites.get(guild_id)
  if everyone is not None:
    value = (value & ~int(everyone.deny)) | int(everyone.allow)
  allow = deny = 0
  for role_id in member.roles:
    if (overwrite := overwrites.get(role_id)) is not None:
      allow |= int(overwrite.allow)
      deny |= int(overwrite.deny)
  value = (value & ~deny) | allow
  if (own := overwrites.get(user_id)) is not None:
    value = (value & ~int(own.deny)) | int(own.allow)
  return value
