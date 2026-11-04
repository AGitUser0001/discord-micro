# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_reference_type import MessageReferenceType
from ._snowflake_type import SnowflakeType


class MessageReferenceRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: SnowflakeType | None = None
    channel_id: SnowflakeType | None = None
    message_id: SnowflakeType
    fail_if_not_exists: bool | None = None
    type: MessageReferenceType | None = None
