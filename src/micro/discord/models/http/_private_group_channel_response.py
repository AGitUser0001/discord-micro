# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._channel_types import ChannelTypes
from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse


class PrivateGroupChannelResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: ChannelTypes
    last_message_id: SnowflakeType | None = None
    flags: int
    last_pin_timestamp: AwareDatetime | None = None
    recipients: list[UserResponse]
    name: str | None
    icon: str | None
    owner_id: SnowflakeType
    managed: bool | None = None
    application_id: SnowflakeType | None = None
