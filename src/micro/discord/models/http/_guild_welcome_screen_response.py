# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_welcome_screen_channel_response import GuildWelcomeScreenChannelResponse


class GuildWelcomeScreenResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    description: str | None
    welcome_channels: list[GuildWelcomeScreenChannelResponse]
