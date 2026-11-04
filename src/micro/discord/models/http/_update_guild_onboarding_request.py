# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_onboarding_mode import GuildOnboardingMode
from ._snowflake_type import SnowflakeType
from ._update_onboarding_prompt_request import UpdateOnboardingPromptRequest


class UpdateGuildOnboardingRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    prompts: Annotated[
        list[UpdateOnboardingPromptRequest] | None, Field(max_length=15)
    ] = None
    enabled: bool | None = None
    default_channel_ids: Annotated[
        list[SnowflakeType] | None, Field(max_length=500)
    ] = None
    mode: GuildOnboardingMode | None = None
