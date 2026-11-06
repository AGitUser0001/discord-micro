"""Invite links: add the bot to a server, or install it on a user's account.

    from micro.discord.invite import Permissions, invite_url

    invite_url("1234", permissions=Permissions.SEND_MESSAGES | Permissions.EMBED_LINKS)
    invite_url("1234", install="user")

`micro invite` prints both for the current project, using the permissions in
the `[invite]` section of micro.toml.
"""

import base64
import binascii
import difflib
from collections.abc import Iterable
from enum import IntFlag
from typing import Literal
from urllib.parse import urlencode

AUTHORIZE_URL = "https://discord.com/oauth2/authorize"


class Permissions(IntFlag):
  """Discord's permission bits (`permissions` in an invite is their sum)."""

  CREATE_INSTANT_INVITE = 1 << 0
  KICK_MEMBERS = 1 << 1
  BAN_MEMBERS = 1 << 2
  ADMINISTRATOR = 1 << 3
  MANAGE_CHANNELS = 1 << 4
  MANAGE_GUILD = 1 << 5
  ADD_REACTIONS = 1 << 6
  VIEW_AUDIT_LOG = 1 << 7
  PRIORITY_SPEAKER = 1 << 8
  STREAM = 1 << 9
  VIEW_CHANNEL = 1 << 10
  SEND_MESSAGES = 1 << 11
  SEND_TTS_MESSAGES = 1 << 12
  MANAGE_MESSAGES = 1 << 13
  EMBED_LINKS = 1 << 14
  ATTACH_FILES = 1 << 15
  READ_MESSAGE_HISTORY = 1 << 16
  MENTION_EVERYONE = 1 << 17
  USE_EXTERNAL_EMOJIS = 1 << 18
  VIEW_GUILD_INSIGHTS = 1 << 19
  CONNECT = 1 << 20
  SPEAK = 1 << 21
  MUTE_MEMBERS = 1 << 22
  DEAFEN_MEMBERS = 1 << 23
  MOVE_MEMBERS = 1 << 24
  USE_VAD = 1 << 25
  CHANGE_NICKNAME = 1 << 26
  MANAGE_NICKNAMES = 1 << 27
  MANAGE_ROLES = 1 << 28
  MANAGE_WEBHOOKS = 1 << 29
  MANAGE_GUILD_EXPRESSIONS = 1 << 30
  USE_APPLICATION_COMMANDS = 1 << 31
  REQUEST_TO_SPEAK = 1 << 32
  MANAGE_EVENTS = 1 << 33
  MANAGE_THREADS = 1 << 34
  CREATE_PUBLIC_THREADS = 1 << 35
  CREATE_PRIVATE_THREADS = 1 << 36
  USE_EXTERNAL_STICKERS = 1 << 37
  SEND_MESSAGES_IN_THREADS = 1 << 38
  USE_EMBEDDED_ACTIVITIES = 1 << 39
  MODERATE_MEMBERS = 1 << 40
  VIEW_CREATOR_MONETIZATION_ANALYTICS = 1 << 41
  USE_SOUNDBOARD = 1 << 42
  CREATE_GUILD_EXPRESSIONS = 1 << 43
  CREATE_EVENTS = 1 << 44
  USE_EXTERNAL_SOUNDS = 1 << 45
  SEND_VOICE_MESSAGES = 1 << 46
  SEND_POLLS = 1 << 49
  USE_EXTERNAL_APPS = 1 << 50
  PIN_MESSAGES = 1 << 51
  BYPASS_SLOWMODE = 1 << 52


def application_id(token: str) -> str:
  """The application ID inside a bot token: its first segment, base64-encoded."""
  segment = token.removeprefix("Bot ").strip().split(".", 1)[0]
  try:
    value = base64.urlsafe_b64decode(segment + "=" * (-len(segment) % 4)).decode()
  except binascii.Error, UnicodeDecodeError:
    value = ""
  if not value.isdecimal():
    raise ValueError("That does not look like a Discord bot token.")
  return value


def parse_permissions(values: Iterable[str | int]) -> Permissions:
  """Names (`send_messages`, `Send Messages`), numbers, or `admin`, combined."""
  result = Permissions(0)
  for value in values:
    if isinstance(value, int):
      result |= Permissions(value)
      continue
    text = value.strip()
    if not text:
      continue
    if text.isdecimal():
      result |= Permissions(int(text))
      continue
    name = text.upper().replace(" ", "_").replace("-", "_")
    name = "ADMINISTRATOR" if name == "ADMIN" else name
    member = Permissions.__members__.get(name)
    if member is None:
      close = difflib.get_close_matches(name, Permissions.__members__, n=1)
      hint = f" Did you mean {close[0].lower()}?" if close else ""
      raise ValueError(f"Unknown permission {value!r}.{hint}")
    result |= member
  return result


def invite_url(
  application: int | str,
  *,
  install: Literal["guild", "user"] = "guild",
  permissions: Permissions | int = 0,
  guild_id: int | str | None = None,
  redirect_uri: str | None = None,
  state: str | None = None,
) -> str:
  """The authorization link for an application.

  `install="guild"` adds the bot to a server (`permissions` it asks for, and
  `guild_id` to preselect and lock the server); `install="user"` installs the
  application's commands on a user's account, which has neither.
  """
  query = {"client_id": str(application)}
  if install == "guild":
    query["scope"] = "bot applications.commands"
    query["integration_type"] = "0"
    if int(permissions):
      query["permissions"] = str(int(permissions))
    if guild_id is not None:
      query["guild_id"] = str(guild_id)
      query["disable_guild_select"] = "true"
  else:
    if int(permissions) or guild_id is not None:
      raise ValueError("A user install has no permissions and no server to preselect.")
    query["scope"] = "applications.commands"
    query["integration_type"] = "1"
  if redirect_uri is not None:
    query["redirect_uri"] = redirect_uri
    query["response_type"] = "code"
  if state is not None:
    query["state"] = state
  return f"{AUTHORIZE_URL}?{urlencode(query)}"


__all__ = (
  "AUTHORIZE_URL",
  "Permissions",
  "application_id",
  "invite_url",
  "parse_permissions",
)
