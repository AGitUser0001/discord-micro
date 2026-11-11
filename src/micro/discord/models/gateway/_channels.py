# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_guild_category_channel_type_o1 import APIGuildCategoryChannelTypeO1
from ._api_guild_forum_channel_type_o1 import APIGuildForumChannelTypeO1
from ._api_guild_media_channel_type_o1 import APIGuildMediaChannelTypeO1
from ._api_guild_voice_channel_type_o1 import APIGuildVoiceChannelTypeO1
from ._api_guild_stage_voice_channel_type_o1 import APIGuildStageVoiceChannelTypeO1
from ._api_text_channel_type_o1 import APITextChannelTypeO1
from ._api_news_channel_type_o1 import APINewsChannelTypeO1


class Channels(
    RootModel[
        APIGuildCategoryChannelTypeO1
        | APIGuildForumChannelTypeO1
        | APIGuildMediaChannelTypeO1
        | APIGuildVoiceChannelTypeO1
        | APIGuildStageVoiceChannelTypeO1
        | APITextChannelTypeO1
        | APINewsChannelTypeO1
    ]
):
    root: Annotated[
        APIGuildCategoryChannelTypeO1
        | APIGuildForumChannelTypeO1
        | APIGuildMediaChannelTypeO1
        | APIGuildVoiceChannelTypeO1
        | APIGuildStageVoiceChannelTypeO1
        | APITextChannelTypeO1
        | APINewsChannelTypeO1,
        Field(discriminator='type'),
    ]
