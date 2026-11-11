# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._interaction_types import InteractionTypes
from ._snowflake_type import SnowflakeType


class InteractionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: InteractionTypes
    activity_instance_id: str | None = None
    response_message_id: SnowflakeType | None = None
    response_message_loading: bool | None = None
    response_message_ephemeral: bool | None = None
    channel_id: SnowflakeType | None = None
    guild_id: SnowflakeType | None = None
