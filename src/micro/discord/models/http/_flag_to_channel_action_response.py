# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._automod_action_type import AutomodActionType
from ._flag_to_channel_action_metadata_response import FlagToChannelActionMetadataResponse


class FlagToChannelActionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: AutomodActionType
    metadata: FlagToChannelActionMetadataResponse
