"""Typed views of Discord objects: just the fields bots use, extras kept."""

from typing import Any, ClassVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from .colour import Colour


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


class User(_View):
  _full = "UserResponse"
  id: str
  accent_colour: Colour | None = Field(
    default=None,
    validation_alias=AliasChoices("accent_color", "accent_colour"),
    serialization_alias="accent_color",
  )
  """The banner colour the user chose, if any; Discord's JSON calls it `accent_color`."""
  username: str = ""
  global_name: str | None = None
  bot: bool = False

  @property
  def mention(self) -> str:
    """The `<@id>` mention string."""
    return f"<@{self.id}>"

  @property
  def display_name(self) -> str:
    """The global name, or the username without one."""
    return self.global_name or self.username


class Member(_View):
  _full = "GuildMemberResponse"
  """A guild member; `user` is filled from the interaction when resolved."""

  user: User | None = None
  roles: list[str] = []
  nick: str | None = None
  permissions: str | None = None

  @property
  def id(self) -> str | None:
    """The member's user id, or None if Discord sent no user."""
    return self.user.id if self.user is not None else None

  @property
  def mention(self) -> str:
    """The `<@id>` mention string."""
    return f"<@{self.id}>"


class Role(_View):
  _full = "GuildRoleResponse"
  id: str
  name: str = ""
  colour: Colour = Field(
    default=Colour(0),
    validation_alias=AliasChoices("color", "colour"),
    serialization_alias="color",
  )
  """The role's colour (0 means none); Discord's JSON calls it `color`."""
  permissions: str = "0"
  position: int = 0

  @property
  def mention(self) -> str:
    """The `<@&id>` mention string."""
    return f"<@&{self.id}>"


class PermissionOverwrite(_View):
  id: str
  type: int
  allow: str = "0"
  deny: str = "0"


class Channel(_View):
  _full = "GetChannelResponse200"
  id: str
  type: int = 0
  name: str | None = None
  guild_id: str | None = None
  parent_id: str | None = None
  permission_overwrites: list[PermissionOverwrite] = []

  @property
  def mention(self) -> str:
    """The `<#id>` mention string."""
    return f"<#{self.id}>"


class Guild(_View):
  _full = "GuildResponse"
  id: str
  name: str = ""
  owner_id: str | None = None
  roles: list[Role] = []


class Attachment(_View):
  _full = "MessageAttachmentResponse"
  id: str
  filename: str = ""
  url: str = ""
  size: int = 0
  content_type: str | None = None


class Message(_View):
  _full = "MessageResponse"
  id: str
  channel_id: str
  guild_id: str | None = None
  content: str = ""
  author: User | None = None
