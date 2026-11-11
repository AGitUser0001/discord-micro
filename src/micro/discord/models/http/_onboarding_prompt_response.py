# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._onboarding_prompt_type import OnboardingPromptType
from ._snowflake_type import SnowflakeType
from ._onboarding_prompt_option_response import OnboardingPromptOptionResponse


class OnboardingPromptResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    title: str
    options: list[OnboardingPromptOptionResponse]
    single_select: bool
    required: bool
    in_onboarding: bool
    type: OnboardingPromptType
