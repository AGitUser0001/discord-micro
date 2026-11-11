# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_guild_media_channel_type import APIGuildMediaChannelType
from ._api_guild_stage_voice_channel_type import APIGuildStageVoiceChannelType
from ._api_guild_voice_channel_type import APIGuildVoiceChannelType
from ._api_news_channel_type import APINewsChannelType
from ._api_text_channel_type import APITextChannelType
from ._api_guild_category_channel_type import APIGuildCategoryChannelType
from ._api_guild_forum_channel_type import APIGuildForumChannelType


class GatewayChannelModifyDispatchData(
    RootModel[
        APIGuildCategoryChannelType
        | APIGuildForumChannelType
        | APIGuildMediaChannelType
        | APIGuildStageVoiceChannelType
        | APIGuildVoiceChannelType
        | APINewsChannelType
        | APITextChannelType
    ]
):
    root: Annotated[
        APIGuildCategoryChannelType
        | APIGuildForumChannelType
        | APIGuildMediaChannelType
        | APIGuildStageVoiceChannelType
        | APIGuildVoiceChannelType
        | APINewsChannelType
        | APITextChannelType,
        Field(discriminator='type'),
    ]
