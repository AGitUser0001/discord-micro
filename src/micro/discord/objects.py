"""Typed views of Discord objects: just the fields bots use, extras kept."""

from datetime import UTC, datetime
from typing import Any, ClassVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .colour import Colour
from .permissions import Permissions

CDN = "https://cdn.discordapp.com"


def _image(path: str, hash: str, size: int | None) -> str:
  """A CDN picture URL: animated ones (hash starting `a_`) as GIF, the rest as PNG."""
  extension = "gif" if hash.startswith("a_") else "png"
  query = f"?size={size}" if size else ""
  return f"{CDN}/{path}/{hash}.{extension}{query}"


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
  avatar: str | None = None
  """The avatar's hash, if the user set one; see `avatar_url`."""

  @property
  def mention(self) -> str:
    """The `<@id>` mention string."""
    return f"<@{self.id}>"

  @property
  def display_name(self) -> str:
    """The global name, or the username without one."""
    return self.global_name or self.username

  def avatar_url(self, size: int | None = None) -> str:
    """The user's avatar, or the default one Discord shows without it.

    `size` is a power of two from 16 to 4096.
    """
    if self.avatar:
      return _image(f"avatars/{self.id}", self.avatar, size)
    return f"{CDN}/embed/avatars/{(int(self.id) >> 22) % 6}.png"


class Member(_View):
  _full = "GuildMemberResponse"
  """A guild member; `user` is filled from the interaction when resolved."""

  user: User | None = None
  roles: list[str] = []
  nick: str | None = None
  permissions: Permissions | None = None
  """The member's permissions where the interaction happened (interactions only)."""
  avatar: str | None = None
  """The hash of the avatar set for this server only, if any."""

  @property
  def id(self) -> str | None:
    """The member's user id, or None if Discord sent no user."""
    return self.user.id if self.user is not None else None

  @property
  def mention(self) -> str:
    """The `<@id>` mention string."""
    return f"<@{self.id}>"

  @property
  def display_name(self) -> str:
    """The server nickname, else the user's display name."""
    return self.nick or (self.user.display_name if self.user is not None else "")


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
  type: int
  allow: Permissions = Permissions.NONE
  deny: Permissions = Permissions.NONE


class Channel(Object):
  _full = "GetChannelResponse200"
  type: int = 0
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
  icon: str | None = None
  """The icon's hash, if the server has one; see `icon_url`."""

  def icon_url(self, size: int | None = None) -> str | None:
    """The server's icon, or None without one (`size`: a power of two, 16 to 4096)."""
    return _image(f"icons/{self.id}", self.icon, size) if self.icon else None


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
