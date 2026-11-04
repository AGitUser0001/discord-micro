"""Typed views of Discord objects: just the fields bots use, extras kept."""

from pydantic import BaseModel, ConfigDict


class _View(BaseModel):
  model_config = ConfigDict(extra="allow", frozen=True)


class User(_View):
  id: str
  username: str = ""
  global_name: str | None = None
  bot: bool = False

  @property
  def mention(self) -> str:
    return f"<@{self.id}>"

  @property
  def display_name(self) -> str:
    return self.global_name or self.username


class Member(_View):
  """A guild member; `user` is filled from the interaction when resolved."""

  user: User | None = None
  roles: list[str] = []
  nick: str | None = None
  permissions: str | None = None

  @property
  def id(self) -> str | None:
    return self.user.id if self.user is not None else None

  @property
  def mention(self) -> str:
    return f"<@{self.id}>"


class Role(_View):
  id: str
  name: str = ""
  permissions: str = "0"
  position: int = 0

  @property
  def mention(self) -> str:
    return f"<@&{self.id}>"


class PermissionOverwrite(_View):
  id: str
  type: int
  allow: str = "0"
  deny: str = "0"


class Channel(_View):
  id: str
  type: int = 0
  name: str | None = None
  guild_id: str | None = None
  parent_id: str | None = None
  permission_overwrites: list[PermissionOverwrite] = []

  @property
  def mention(self) -> str:
    return f"<#{self.id}>"


class Guild(_View):
  id: str
  name: str = ""
  owner_id: str | None = None
  roles: list[Role] = []


class Attachment(_View):
  id: str
  filename: str = ""
  url: str = ""
  size: int = 0
  content_type: str | None = None


class Message(_View):
  id: str
  channel_id: str
  guild_id: str | None = None
  content: str = ""
  author: User | None = None
