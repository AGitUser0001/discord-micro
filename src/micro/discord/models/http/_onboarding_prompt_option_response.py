# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._settings_emoji_response import SettingsEmojiResponse


class OnboardingPromptOptionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    title: str
    description: str
    emoji: SettingsEmojiResponse
    role_ids: list[SnowflakeType]
    channel_ids: list[SnowflakeType]
