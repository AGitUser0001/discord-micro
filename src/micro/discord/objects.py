"""Typed views of Discord objects: just the fields bots use, extras kept."""

from datetime import UTC, datetime
from typing import Any, ClassVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

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


class User(Object):
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


class Member(_View):
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


class Role(Object):
  _full = "GuildRoleResponse"
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


class PermissionOverwrite(Object):
  type: OverwriteType
  allow: Permissions = Permissions.NONE
  deny: Permissions = Permissions.NONE


class Channel(Object):
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


class Guild(Object):
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


class Attachment(Object):
  _full = "MessageAttachmentResponse"
  filename: str = ""
  url: str = ""
  size: int = 0
  content_type: str | None = None


class Message(Object):
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
