# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._onboarding_prompt_type import OnboardingPromptType
from ._snowflake_type import SnowflakeType
from ._onboarding_prompt_option_request import OnboardingPromptOptionRequest


class UpdateOnboardingPromptRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    title: Annotated[str, Field(max_length=100, min_length=1)]
    options: Annotated[
        list[OnboardingPromptOptionRequest], Field(max_length=50, min_length=1)
    ]
    single_select: bool | None = None
    required: bool | None = None
    in_onboarding: bool | None = None
    type: OnboardingPromptType | None = None
    id: SnowflakeType
