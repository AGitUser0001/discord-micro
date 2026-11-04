# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_onboarding_mode import GuildOnboardingMode
from ._snowflake_type import SnowflakeType
from ._onboarding_prompt_response import OnboardingPromptResponse


class UserGuildOnboardingResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: SnowflakeType
    prompts: list[OnboardingPromptResponse]
    default_channel_ids: list[SnowflakeType]
    enabled: bool
    mode: GuildOnboardingMode
