# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_features import GuildFeatures
from ._snowflake_type import SnowflakeType
from ._emoji_response import EmojiResponse
from ._guild_sticker_response import GuildStickerResponse


class GuildPreviewResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    icon: str | None
    description: str | None
    home_header: str | None
    splash: str | None
    discovery_splash: str | None
    features: list[GuildFeatures]
    approximate_member_count: int
    approximate_presence_count: int
    emojis: list[EmojiResponse]
    stickers: list[GuildStickerResponse]
