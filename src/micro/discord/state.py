"""What the Gateway connections know of Discord, asked for: reads of the live state.

A guild lives on exactly one shard (`(guild_id >> 22) % shard_count`), and the connection
serving that shard holds its roles, channels and members in memory. `DiscordState` asks
that connection:

    state = DiscordState(runtime)
    role = await state.role(role_id)                    # no guild needed
    channels = await state.channels(guild_id)
    member = await state.member(guild_id, user_id)
    allowed = await state.permissions(guild_id, user_id, channel_id)

    user = await state.user(user_id)                    # the same in every guild
    for known in await state.mutual_guilds(user_id):    # the guilds we know it is in
      member = await known.member()

A read answers from what the connection holds or says it has nothing (`None`). It never
asks Discord: what to do about a miss (fetch it through the API, treat it as not there)
is the caller's decision. `None` means "state does not know", which is not the same as
"it does not exist": a guild whose shard is down, reconnecting or not yet handed over
holds nothing until it is back, and members are only known to the extent events and the
`guild_members` intent have delivered them.

Anything that is not about one guild (a user, a role or channel by id alone) is asked of
every shard at once: whichever shards know it answer, and the newest copy of a user wins.
A shard that is down simply does not contribute.
"""

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING

from nats.errors import NoRespondersError
from nats.errors import TimeoutError as NatsTimeoutError
from pydantic import JsonValue
from pydantic_core import from_json, to_json

from micro import subjects
from micro.discord.objects import Channel, Guild, Member, Role, User
from micro.discord.permissions import Permissions
from micro.errors import RoutingError

if TYPE_CHECKING:
  from micro.runtime import Runtime

ADMINISTRATOR = Permissions.ADMINISTRATOR
ALL_PERMISSIONS = Permissions((1 << 53) - 1)
"""Every permission bit Discord can define (JSON-safe integer range)."""


@dataclass(frozen=True, slots=True)
class KnownGuild:
  """A guild the state knows a user is in: `member()` is that user there."""

  guild: Guild
  user_id: str
  state: DiscordState

  async def member(self) -> Member | None:
    """The user as a member of this guild."""
    return await self.state.member(self.guild.id, self.user_id)


class DiscordState:
  """Reads of what the Gateway connections hold (they are asked, nothing is stored).

  Every method returns what the connections know, or `None`. A missing shard is not an
  error: it just knows nothing right now.
  """

  def __init__(self, runtime: Runtime) -> None:
    from micro.gateway import GatewayControl

    self.runtime = runtime
    self._control = GatewayControl(runtime)

  async def guild(self, guild_id: int | str) -> Guild | None:
    """The guild itself (its name, owner, settings). Its roles, channels and members
    are read with `roles`, `channels` and `member`."""
    payload = await self._ask_guild(guild_id, "guild")
    return Guild.model_validate(payload) if isinstance(payload, dict) else None

  async def roles(self, guild_id: int | str) -> list[Role] | None:
    """Every role of the guild, or None while the guild is not held."""
    payloads = await self._ask_guild(guild_id, "roles")
    if not isinstance(payloads, list):
      return None
    return [Role.model_validate(p) for p in payloads if isinstance(p, dict)]

  async def role(self, role_id: int | str) -> Role | None:
    """A role by id alone."""
    found = await self._where("role", role_id)
    return None if found is None else Role.model_validate(found[1])

  async def channels(self, guild_id: int | str) -> list[Channel] | None:
    """Every channel of the guild, or None while the guild is not held."""
    payloads = await self._ask_guild(guild_id, "channels")
    if not isinstance(payloads, list):
      return None
    return [
      Channel.model_validate({"guild_id": str(guild_id), **p})
      for p in payloads
      if isinstance(p, dict)
    ]

  async def channel(self, channel_id: int | str) -> Channel | None:
    """A channel by id alone (it knows its guild)."""
    found = await self._where("channel", channel_id)
    if found is None:
      return None
    return Channel.model_validate({"guild_id": found[0], **found[1]})

  async def user(self, user_id: int | str) -> User | None:
    """A user, the same in every guild: the newest copy any shard holds."""
    newest: tuple[int, dict[str, JsonValue]] | None = None
    for answer in await self._ask_all("user", user_id=str(user_id)):
      if not isinstance(answer, dict):
        continue
      stamp, payload = answer.get("stamp"), answer.get("payload")
      if (
        isinstance(stamp, int)
        and isinstance(payload, dict)
        and (newest is None or stamp > newest[0])
      ):
        newest = (stamp, payload)
    return None if newest is None else User.model_validate(newest[1])

  async def mutual_guilds(self, user_id: int | str) -> list[KnownGuild]:
    """The guilds the shards know this user to be in, each with `member()` for the user
    there. Like discord.py's `User.mutual_guilds` this is computed from what is held, so
    it is only the members the shards have seen (the member list needs the
    `guild_members` intent), and a guild whose shard is down is missing."""
    guilds: list[KnownGuild] = []
    for answer in await self._ask_all("guilds_of", user_id=str(user_id)):
      for payload in answer if isinstance(answer, list) else []:
        if isinstance(payload, dict):
          guilds.append(KnownGuild(Guild.model_validate(payload), str(user_id), self))
    return guilds

  async def member(self, guild_id: int | str, user_id: int | str) -> Member | None:
    """A guild member, with its `user` filled in. A user is a different member in each
    guild, and the same user in all of them."""
    payload = await self._ask_guild(guild_id, "member", user_id=str(user_id))
    if not isinstance(payload, dict):
      return None
    return Member.model_validate({**payload, "guild_id": str(guild_id)})

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

  # Asking the shards -----------------------------------------------------------

  async def _ask(
    self, shard_id: int, operation: str, **arguments: JsonValue
  ) -> JsonValue:
    """One question to one shard's connection: its answer, or None if there is none."""
    body = to_json({"operation": operation, **arguments})
    try:
      reply = await self.runtime.request(
        subjects.state(shard_id), body, timeout=self._control.timeout
      )
    except NoRespondersError, NatsTimeoutError:
      return None  # nobody serves that shard right now
    return from_json(reply.data)

  async def _ask_guild(
    self, guild_id: int | str, operation: str, **arguments: JsonValue
  ) -> JsonValue:
    """A question about one guild, asked of the one shard that holds it."""
    try:
      shard_id = await self._control.shard_for(int(guild_id))
    except RoutingError:
      return None
    return await self._ask(shard_id, operation, guild_id=str(guild_id), **arguments)

  async def _ask_all(self, operation: str, **arguments: JsonValue) -> list[JsonValue]:
    """A question asked of every shard at once; the answers of those that gave one."""
    try:
      count = await self._control.shard_count()
    except RoutingError:
      return []
    answers = await asyncio.gather(
      *(self._ask(shard, operation, **arguments) for shard in range(count))
    )
    return [answer for answer in answers if answer is not None]

  async def _where(
    self, kind: str, object_id: int | str
  ) -> tuple[str, dict[str, JsonValue]] | None:
    """An object with a globally unique id (a channel, a role): its guild and payload."""
    for answer in await self._ask_all(kind, id=str(object_id)):
      if isinstance(answer, dict) and isinstance(
        payload := answer.get("payload"), dict
      ):
        return str(answer["guild_id"]), payload
    return None


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


__all__ = (
  "ALL_PERMISSIONS",
  "DiscordState",
  "KnownGuild",
  "compute_permissions",
)
