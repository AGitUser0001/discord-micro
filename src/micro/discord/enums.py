"""Discord's numbered kinds, as enums: `ChannelType.GUILD_VOICE` rather than `2`.

These are the enums Discord's own specification defines (generated with the models in
`micro.discord.models.http`), under their singular names, so a new Discord release adds
their members on regeneration. They are `IntEnum`s: equal to the numbers Discord sends, and
sent as those numbers. Micro makes them accept a number it does not list (one Discord added
since): it becomes a member named `UNKNOWN_<n>` instead of failing to read an object.

    channel.type is ChannelType.GUILD_TEXT
    ChannelSelect("pick", channel_types=[ChannelType.GUILD_TEXT, ChannelType.GUILD_VOICE])
    Button("Delete", custom_id="del", style=ButtonStyle.DANGER)
    CommandType.CHAT                 # a slash command (Discord calls it chat input)
"""

from enum import IntEnum

from micro.discord.models.http import ApplicationCommandType as CommandType
from micro.discord.models.http import ButtonStyleTypes as ButtonStyle
from micro.discord.models.http import ChannelPermissionOverwrites as OverwriteType
from micro.discord.models.http import ChannelTypes as ChannelType
from micro.discord.models.http import InteractionTypes as InteractionType
from micro.discord.models.http import TextInputStyleTypes as TextInputStyle


def _open(kind: type[IntEnum]) -> None:
  """Make the enum keep a number it does not know, rather than refuse it."""

  def missing(cls: type[IntEnum], value: object) -> IntEnum | None:
    if not isinstance(value, int) or isinstance(value, bool):
      return None
    unknown = int.__new__(cls, value)
    unknown._name_ = f"UNKNOWN_{value}"
    unknown._value_ = value
    return cls._value2member_map_.setdefault(value, unknown)  # pyright: ignore[reportReturnType]

  kind._missing_ = classmethod(missing)  # type: ignore[method-assign,assignment]


for _kind in (
  ChannelType,
  OverwriteType,
  InteractionType,
  CommandType,
  ButtonStyle,
  TextInputStyle,
):
  _open(_kind)

__all__ = (
  "ButtonStyle",
  "ChannelType",
  "CommandType",
  "InteractionType",
  "OverwriteType",
  "TextInputStyle",
)
