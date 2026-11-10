"""Discord's state as every shard sees it, aggregated: reads of the projection.

The Gateway delivers a guild's roles, channels and members to whichever shard owns it,
and the shards come and go. `GatewayProjection` folds all of it into one view that does
not depend on which shard or connection delivered what, and `DiscordState` reads that
view:

    state = DiscordState(runtime)
    role = await state.role(role_id)                    # no guild needed
    channels = await state.channels(guild_id)
    member = await state.member(guild_id, user_id)
    allowed = await state.permissions(guild_id, user_id, channel_id)

A read answers from the aggregation or says it has nothing (`None`). It never asks
Discord: what to do about a miss (fetch it through the API, treat it as not there) is the
caller's decision. `None` means "the aggregation does not hold it", which is not the same
as "it does not exist": a guild that is not current (its connection has a gap) holds
nothing until it is, and members are only known to the extent events and the
`guild_members` intent have delivered them.
"""

from typing import TYPE_CHECKING

from pydantic import JsonValue

from micro.discord.objects import Channel, Guild, Member, Role
from micro.discord.permissions import Permissions

if TYPE_CHECKING:
  from micro.runtime import Runtime

ADMINISTRATOR = Permissions.ADMINISTRATOR
ALL_PERMISSIONS = Permissions((1 << 53) - 1)
"""Every permission bit Discord can define (JSON-safe integer range)."""


class DiscordState:
  """Reads of the aggregated Discord state (run `GatewayProjection` and a `Store`).

  Every method returns what the aggregation holds, or `None`. The store being
  unreachable is not a miss: that raises (`RoutingError`).
  """

  def __init__(self, runtime: Runtime) -> None:
    from micro.store import StoreClient

    self.runtime = runtime
    self._store = StoreClient(runtime)

  async def guild(self, guild_id: int | str) -> Guild | None:
    """The guild itself (its name, owner, settings). Its roles, channels and members
    are read with `roles`, `channels` and `member`."""
    payload = await self._object(str(guild_id), "guild", str(guild_id))
    return None if payload is None else Guild.model_validate(payload)

  async def roles(self, guild_id: int | str) -> list[Role] | None:
    """Every role of the guild, or None unless the guild's full state was received and
    is current."""
    payloads = await self._listing(str(guild_id), "roles")
    return None if payloads is None else [Role.model_validate(p) for p in payloads]

  async def role(self, role_id: int | str) -> Role | None:
    """A role by id alone."""
    found = await self._by_id("role", str(role_id))
    return None if found is None else Role.model_validate(found[1])

  async def channels(self, guild_id: int | str) -> list[Channel] | None:
    """Every channel of the guild, or None unless the guild's full state was received and
    is current."""
    payloads = await self._listing(str(guild_id), "channels")
    if payloads is None:
      return None
    return [Channel.model_validate({"guild_id": str(guild_id), **p}) for p in payloads]

  async def channel(self, channel_id: int | str) -> Channel | None:
    """A channel by id alone (it knows its guild)."""
    found = await self._by_id("channel", str(channel_id))
    if found is None:
      return None
    guild_id, payload = found
    return Channel.model_validate({"guild_id": guild_id, **payload})

  async def member(self, guild_id: int | str, user_id: int | str) -> Member | None:
    """A guild member. A user is a different member in each guild."""
    payload = await self._object(str(guild_id), "member", f"{guild_id}:{user_id}")
    return None if payload is None else Member.model_validate(payload)

  async def permissions(
    self,
    guild_id: int | str,
    user_id: int | str,
    channel_id: int | str | None = None,
  ) -> Permissions | None:
    """A member's effective permissions, in a channel if given; None unless the guild,
    its roles, the member (and the channel) are all held."""
    guild = await self.guild(guild_id)
    roles = await self.roles(guild_id)
    member = await self.member(guild_id, user_id)
    if guild is None or roles is None or member is None:
      return None
    channel = None
    if channel_id is not None:
      channel = await self.channel(channel_id)
      if channel is None:
        return None
    return compute_permissions(
      str(guild_id), guild.owner_id, roles, member, str(user_id), channel
    )

  # Reading the projection -------------------------------------------------------

  async def _object(
    self, guild_id: str, kind: str, object_id: str
  ) -> dict[str, JsonValue] | None:
    """One object of a guild, if the guild is current."""
    data = await self._read(
      """
      query Read($guild: ID!, $kind: String!, $id: ID!) {
        guild: gatewayGuild(id: $guild) { fresh }
        object: discordObject(guildId: $guild, kind: $kind, id: $id) { payload }
      }
      """,
      {"guild": guild_id, "kind": kind, "id": object_id},
    )
    guild, found = data.get("guild"), data.get("object")
    if not (isinstance(guild, dict) and guild.get("fresh") is True):
      return None
    payload = found.get("payload") if isinstance(found, dict) else None
    return payload if isinstance(payload, dict) else None

  async def _by_id(
    self, kind: str, object_id: str
  ) -> tuple[str, dict[str, JsonValue]] | None:
    """An object with a globally unique id (a channel, a role): its guild, found
    through the index, and its payload."""
    data = await self._read(
      "query Where($kind: String!, $id: ID!) { where: discordIndex(kind: $kind, id: $id)"
      " { guildId } }",
      {"kind": kind, "id": object_id},
    )
    where = data.get("where")
    guild_id = where.get("guildId") if isinstance(where, dict) else None
    if not isinstance(guild_id, str):
      return None
    payload = await self._object(guild_id, kind, object_id)
    return None if payload is None else (guild_id, payload)

  async def _listing(
    self, guild_id: str, field: str
  ) -> list[dict[str, JsonValue]] | None:
    """A complete list (`roles`, `channels`) of a guild, if it is current and synced."""
    data = await self._read(
      f"query List($guild: ID!) {{ guild: gatewayGuild(id: $guild) "
      f"{{ fresh synced {field} {{ payload }} }} }}",
      {"guild": guild_id},
    )
    guild = data.get("guild")
    if not (
      isinstance(guild, dict)
      and guild.get("fresh") is True
      and guild.get("synced") is True
    ):
      return None
    items = guild.get(field)
    if not isinstance(items, list):
      return None
    payloads: list[dict[str, JsonValue]] = []
    for item in items:
      payload = item.get("payload") if isinstance(item, dict) else None
      if isinstance(payload, dict):
        payloads.append(payload)
    return payloads

  async def _read(
    self, query: str, variables: dict[str, JsonValue]
  ) -> dict[str, JsonValue]:
    result = await self._store.execute(query, variables=variables)
    data = result.get("data")
    return data if isinstance(data, dict) else {}


def compute_permissions(
  guild_id: str,
  owner_id: str | None,
  roles: list[Role],
  member: Member,
  user_id: str,
  channel: Channel | None = None,
) -> Permissions:
  """Discord's permission algorithm: roles, administrator, then overwrites."""
  return Permissions(_compute(guild_id, owner_id, roles, member, user_id, channel))


def _compute(
  guild_id: str,
  owner_id: str | None,
  roles: list[Role],
  member: Member,
  user_id: str,
  channel: Channel | None,
) -> int:
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


__all__ = ("ALL_PERMISSIONS", "DiscordState", "compute_permissions")
