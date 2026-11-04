# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._channel_types import ChannelTypes
from ._snowflake_type import SnowflakeType
from ._invite_channel_recipient_response import InviteChannelRecipientResponse


class InviteChannelResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: ChannelTypes
    name: str | None
    icon: str | None = None
    recipients: list[InviteChannelRecipientResponse] | None = None
