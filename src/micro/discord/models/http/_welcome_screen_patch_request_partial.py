# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_welcome_channel import GuildWelcomeChannel


class WelcomeScreenPatchRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    description: Annotated[str | None, Field(max_length=140)] = None
    welcome_channels: Annotated[
        list[GuildWelcomeChannel] | None, Field(max_length=5)
    ] = None
    enabled: bool | None = None
