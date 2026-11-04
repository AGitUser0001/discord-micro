# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class UpdateVoiceChannelStatusRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    status: Annotated[
        str | None, Field(description='The new voice channel status', max_length=500)
    ] = None
