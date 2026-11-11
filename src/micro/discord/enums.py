"""Discord's numbered kinds, as enums: `ChannelType.GUILD_VOICE` rather than `2`.

They are `IntEnum`s, so they compare equal to the numbers Discord sends and are sent as
those numbers. A number Discord adds after this release is still accepted: it becomes a
member named `UNKNOWN_<n>`, so a new kind never breaks reading an object.

    channel.type is ChannelType.GUILD_TEXT
    ChannelSelect("pick", channel_types=[ChannelType.GUILD_TEXT, ChannelType.GUILD_VOICE])
    Button("Delete", custom_id="del", style=ButtonStyle.DANGER)
"""

from enum import IntEnum
from typing import Self


class _Open(IntEnum):
  """An enum that keeps a number it does not know instead of refusing it."""

  @classmethod
  def _missing_(cls, value: object) -> Self | None:
    if not isinstance(value, int) or isinstance(value, bool):
      return None
    unknown = int.__new__(cls, value)
    unknown._name_ = f"UNKNOWN_{value}"
    unknown._value_ = value
    return cls._value2member_map_.setdefault(value, unknown)  # pyright: ignore[reportReturnType]


class ChannelType(_Open):
  """What kind of channel it is."""

  GUILD_TEXT = 0
  DM = 1
  GUILD_VOICE = 2
  GROUP_DM = 3
  GUILD_CATEGORY = 4
  GUILD_ANNOUNCEMENT = 5
  ANNOUNCEMENT_THREAD = 10
  PUBLIC_THREAD = 11
  PRIVATE_THREAD = 12
  GUILD_STAGE_VOICE = 13
  GUILD_DIRECTORY = 14
  GUILD_FORUM = 15
  GUILD_MEDIA = 16

  @property
  def is_thread(self) -> bool:
    """Whether it is one of the three kinds of thread."""
    return self in (
      ChannelType.ANNOUNCEMENT_THREAD,
      ChannelType.PUBLIC_THREAD,
      ChannelType.PRIVATE_THREAD,
    )

  @property
  def is_voice(self) -> bool:
    """Whether people join it to talk: a voice or a stage channel."""
    return self in (ChannelType.GUILD_VOICE, ChannelType.GUILD_STAGE_VOICE)


class OverwriteType(_Open):
  """Whom a channel's permission overwrite is for."""

  ROLE = 0
  MEMBER = 1


class InteractionType(_Open):
  """What the user did to produce an interaction."""

  PING = 1
  APPLICATION_COMMAND = 2
  MESSAGE_COMPONENT = 3
  APPLICATION_COMMAND_AUTOCOMPLETE = 4
  MODAL_SUBMIT = 5


class CommandType(_Open):
  """How a command is invoked."""

  SLASH = 1
  USER = 2
  MESSAGE = 3


class ButtonStyle(_Open):
  """How a button looks and what it does. A button with a `url` is always `LINK`, and one
  with a `sku_id` always `PREMIUM`."""

  PRIMARY = 1
  SECONDARY = 2
  SUCCESS = 3
  DANGER = 4
  LINK = 5
  PREMIUM = 6


class TextInputStyle(_Open):
  """One line, or a paragraph."""

  SHORT = 1
  PARAGRAPH = 2


__all__ = (
  "ButtonStyle",
  "ChannelType",
  "CommandType",
  "InteractionType",
  "OverwriteType",
  "TextInputStyle",
)
