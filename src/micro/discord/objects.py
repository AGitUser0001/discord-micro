"""Typed views of Discord objects: just the fields bots use, extras kept."""

from datetime import UTC, datetime
from typing import Any, ClassVar, Self

from pydantic import (
  AliasChoices,
  BaseModel,
  ConfigDict,
  Field,
  PrivateAttr,
  model_validator,
)

from ._actions import (
  ChannelActions,
  GuildActions,
  MemberActions,
  MessageActions,
  RoleActions,
  UserActions,
)
from .asset import Asset
from .colour import Colour
from .enums import ChannelType, OverwriteType
from .permissions import Permissions


def _created(snowflake: str) -> datetime:
  return datetime.fromtimestamp(((int(snowflake) >> 22) + 1420070400000) / 1000, UTC)


class _View(BaseModel):
  """A slim, forgiving view of a Discord object. Every other field Discord sent stays
  on it as an attribute (`message.pinned`, `user.banner`); `full()` types them all. Fields Discord spells `color` are `colour` here
  (`role.colour`, `user.accent_colour`) and still read and write `color` on the wire."""

  model_config = ConfigDict(extra="allow", frozen=True, populate_by_name=True)
  _full: ClassVar[str | None] = None
  _context: Any = PrivateAttr(default=None)

  def bind(self, context: Any) -> Self:
    """This object tied to a `Context`, so its actions (`reply`, `ban`, ...) work."""
    bound = self.model_copy()
    bound._context = context
    return bound

  @property
  def context(self) -> Any:
    """The `Context` this object is bound to (an object you build by hand has none).

    Raises:
      RuntimeError: The object is not bound to a context.
    """
    if self._context is None:
      raise RuntimeError(
        f"This {type(self).__name__} is not bound to a Context: objects handed to a "
        "handler or read from `ctx.state` are; one you built by hand is not."
      )
    return self._context

  def full(self) -> Any:
    """Everything Discord sent, as Discord's own generated model for this object.

    Raises `ValidationError` if the payload was partial (a resolved member has no
    `user` of its own, for instance).
    """
    from pydantic import TypeAdapter

    from micro.discord.models import http

    if self._full is None:
      raise TypeError(f"{type(self).__name__} has no full model.")
    return TypeAdapter(getattr(http, self._full)).validate_python(
      self.model_dump(mode="json", by_alias=True)
    )


def _assets(data: Any, folder: str, *fields: str) -> Any:
  """Turn the picture hashes Discord sent (`avatar`, `icon`) into `Asset`s, which need the
  id of the object they belong to for their address."""
  if not isinstance(data, dict) or not isinstance(data.get("id"), str):
    return data
  made = {
    field: Asset(f"{folder}/{data['id']}", data[field])
    for field in fields
    if isinstance(data.get(field), str) and data[field]
  }
  return {**data, **made} if made else data


class Object(_View):
  """The root of every Discord object that has an id: users, roles, channels, servers,
  messages, attachments. Ids are snowflakes, which also say when the thing was created.
  Two objects of one kind are equal when their ids are."""

  id: str

  @property
  def snowflake(self) -> int:
    """The id as a number."""
    return int(self.id)

  @property
  def created_at(self) -> datetime:
    """When this object was created (read from its id)."""
    return _created(self.id)

  def __eq__(self, other: object) -> bool:
    return type(other) is type(self) and other.id == self.id  # pyright: ignore[reportAttributeAccessIssue]

  def __hash__(self) -> int:
    return hash((type(self).__name__, self.id))


class User(Object, UserActions):
  _full = "UserResponse"
  accent_colour: Colour | None = Field(
    default=None,
    validation_alias=AliasChoices("accent_color", "accent_colour"),
    serialization_alias="accent_color",
  )
  """The banner colour the user chose, if any; Discord's JSON calls it `accent_color`."""
  username: str = ""
  global_name: str | None = None
  bot: bool = False
  avatar: Asset | None = None
  """The picture the user set, if any (`display_avatar` falls back to the default)."""

  @model_validator(mode="before")
  @classmethod
  def _pictures(cls, data: Any) -> Any:
    return _assets(data, "avatars", "avatar")

  @property
  def mention(self) -> str:
    """The `<@id>` mention string."""
    return f"<@{self.id}>"

  @property
  def display_name(self) -> str:
    """The global name, or the username without one."""
    return self.global_name or self.username

  @property
  def default_avatar(self) -> Asset:
    """The avatar Discord shows for a user without one (it depends on the id)."""
    return Asset("embed/avatars", str((int(self.id) >> 22) % 6), format="png")

  @property
  def display_avatar(self) -> Asset:
    """The avatar the user set, or the default one."""
    return self.avatar or self.default_avatar


class Member(_View, MemberActions):
  """A user in one guild. Its identity is the pair, `(guild_id, user id)`: one user is a
  different member in every guild, and the same user in all of them (`user`).

  Discord's JSON leaves both out of a member it sends inside a guild or a resolved
  interaction, so Micro fills them in; build one yourself with both."""

  _full = "GuildMemberResponse"

  guild_id: str
  """The guild this is a member of: half of what a member is."""
  user: User
  """The person: the same in every guild. Its `id` is the other half."""
  roles: list[str] = []
  nick: str | None = None
  permissions: Permissions | None = None
  """The member's permissions where the interaction happened (interactions only)."""
  avatar: Asset | None = None
  """The picture set for this guild only, if any (`user.display_avatar` is the global one)."""

  @model_validator(mode="before")
  @classmethod
  def _pictures(cls, data: Any) -> Any:
    if not isinstance(data, dict) or not isinstance(data.get("avatar"), str):
      return data
    user = data.get("user")
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    guild_id = data.get("guild_id")
    if not (guild_id and user_id):
      return data  # validation reports the missing guild_id or user
    path = f"guilds/{guild_id}/users/{user_id}/avatars"
    return {**data, "avatar": Asset(path, data["avatar"])}

  @property
  def id(self) -> str:
    """The member's user id."""
    return self.user.id

  @property
  def mention(self) -> str:
    """The `<@id>` mention string."""
    return f"<@{self.id}>"

  @property
  def display_name(self) -> str:
    """The server nickname, else the user's display name."""
    return self.nick or self.user.display_name

  @property
  def display_avatar(self) -> Asset:
    """The picture set for this guild, else the user's own."""
    return self.avatar or self.user.display_avatar

  def __eq__(self, other: object) -> bool:
    return (
      isinstance(other, Member)
      and other.guild_id == self.guild_id
      and other.id == self.id
    )

  def __hash__(self) -> int:
    return hash(("Member", self.guild_id, self.id))

  async def get_guild(self) -> Guild | None:
    """The guild this member is in, from what the Gateway holds."""
    return await self.context.state.guild(self.guild_id)

  async def get_roles(self) -> list[Role]:
    """The member's roles as `Role` objects (those the Gateway holds)."""
    held = await self.context.state.roles(self.guild_id) or []
    return [role for role in held if role.id in self.roles or role.id == self.guild_id]

  async def get_permissions(
    self, channel_id: int | str | None = None
  ) -> Permissions | None:
    """The member's effective permissions, in a channel if given (`None` if not held)."""
    return await self.context.state.permissions(self.guild_id, self.id, channel_id)


class Role(Object, RoleActions):
  _full = "GuildRoleResponse"
  guild_id: str | None = None
  """The guild this role is in (Micro fills it in where it builds a role; its actions
  need it)."""
  name: str = ""
  colour: Colour = Field(
    default=Colour(0),
    validation_alias=AliasChoices("color", "colour"),
    serialization_alias="color",
  )
  """The role's colour (0 means none); Discord's JSON calls it `color`."""
  permissions: Permissions = Permissions.NONE
  position: int = 0

  @property
  def mention(self) -> str:
    """The `<@&id>` mention string."""
    return f"<@&{self.id}>"

  async def get_guild(self) -> Guild | None:
    """The guild this role is in (`None` if it does not know, or the guild is not held)."""
    return (
      None if self.guild_id is None else await self.context.state.guild(self.guild_id)
    )


class PermissionOverwrite(Object):
  type: OverwriteType
  allow: Permissions = Permissions.NONE
  deny: Permissions = Permissions.NONE


class Channel(Object, ChannelActions):
  _full = "GetChannelResponse200"
  type: ChannelType = ChannelType.GUILD_TEXT
  name: str | None = None
  guild_id: str | None = None
  parent_id: str | None = None
  permission_overwrites: list[PermissionOverwrite] = []

  @property
  def mention(self) -> str:
    """The `<#id>` mention string."""
    return f"<#{self.id}>"

  async def get_guild(self) -> Guild | None:
    """The guild this channel is in (`None` for a DM, or if not held)."""
    return (
      None if self.guild_id is None else await self.context.state.guild(self.guild_id)
    )

  async def get_parent(self) -> Channel | None:
    """The category (or the channel, for a thread) this channel sits under."""
    return (
      None
      if self.parent_id is None
      else await self.context.state.channel(self.parent_id)
    )

  async def permissions_for(self, user_id: int | str) -> Permissions | None:
    """A user's effective permissions in this channel (`None` if not held)."""
    if self.guild_id is None:
      return None
    return await self.context.state.permissions(self.guild_id, user_id, self.id)


class Guild(Object, GuildActions):
  _full = "GuildResponse"
  name: str = ""
  owner_id: str | None = None
  roles: list[Role] = []
  icon: Asset | None = None
  """The server's icon, if it has one."""

  @model_validator(mode="before")
  @classmethod
  def _pictures(cls, data: Any) -> Any:
    return _assets(data, "icons", "icon")

  async def get_members(self) -> list[Member] | None:
    """The members the Gateway holds for this guild."""
    return await self.context.state.members(self.id)

  async def get_roles(self) -> list[Role] | None:
    """The guild's roles as the Gateway holds them."""
    return await self.context.state.roles(self.id)

  async def get_channels(self) -> list[Channel] | None:
    """The guild's channels as the Gateway holds them."""
    return await self.context.state.channels(self.id)

  async def get_member(self, user_id: int | str) -> Member | None:
    """One member of this guild, from what the Gateway holds."""
    return await self.context.state.member(self.id, user_id)

  async def get_channel(self, channel_id: int | str) -> Channel | None:
    """One channel by id, from what the Gateway holds."""
    return await self.context.state.channel(channel_id)

  async def get_role(self, role_id: int | str) -> Role | None:
    """One role by id, from what the Gateway holds."""
    return await self.context.state.role(role_id)


class GuildEmoji(Object):
  """A custom emoji of a guild."""

  _full = "EmojiResponse"
  name: str | None = None
  animated: bool = False
  managed: bool = False
  available: bool = True
  roles: list[str] = []


class Sticker(Object):
  """A custom sticker of a guild."""

  _full = "GuildStickerResponse"
  name: str = ""
  description: str | None = None


class StageInstance(Object):
  """A live stage in a stage channel."""

  guild_id: str | None = None
  channel_id: str | None = None
  topic: str = ""


class ScheduledEvent(Object):
  """An event scheduled in a guild."""

  guild_id: str | None = None
  channel_id: str | None = None
  name: str = ""
  description: str | None = None
  scheduled_start_time: str | None = None
  scheduled_end_time: str | None = None


class VoiceState(_View):
  """Where a user is in voice, and how: its guild and user make its identity."""

  guild_id: str
  user_id: str
  channel_id: str | None = None
  session_id: str = ""
  deaf: bool = False
  mute: bool = False
  self_deaf: bool = False
  self_mute: bool = False
  self_stream: bool = False
  self_video: bool = False
  suppress: bool = False


class Presence(_View):
  """A user's status and activities in a guild."""

  guild_id: str | None = None
  status: str = "offline"
  activities: list[dict[str, Any]] = []
  client_status: dict[str, str] = {}
  user: dict[str, Any] = {}


class Attachment(Object):
  _full = "MessageAttachmentResponse"
  filename: str = ""
  url: str = ""
  size: int = 0
  content_type: str | None = None


class Message(Object, MessageActions):
  _full = "MessageResponse"
  channel_id: str
  guild_id: str | None = None
  content: str = ""
  author: User | None = None
  attachments: list[Attachment] = []
  """The files on the message."""

  @property
  def jump_url(self) -> str:
    """A link that opens Discord at this message."""
    return (
      f"https://discord.com/channels/{self.guild_id or '@me'}"
      f"/{self.channel_id}/{self.id}"
    )

  async def get_channel(self) -> Channel | None:
    """The channel this message is in, from what the Gateway holds."""
    return await self.context.state.channel(self.channel_id)

  async def get_guild(self) -> Guild | None:
    """The guild this message is in (`None` for a DM, or if not held)."""
    return (
      None if self.guild_id is None else await self.context.state.guild(self.guild_id)
    )
