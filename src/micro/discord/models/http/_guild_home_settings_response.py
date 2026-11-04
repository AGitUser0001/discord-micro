# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._welcome_message_response import WelcomeMessageResponse
from ._new_member_action_response import NewMemberActionResponse
from ._resource_channel_response import ResourceChannelResponse


class GuildHomeSettingsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: SnowflakeType
    enabled: bool
    welcome_message: WelcomeMessageResponse | None = None
    new_member_actions: list[NewMemberActionResponse]
    resource_channels: list[ResourceChannelResponse]
