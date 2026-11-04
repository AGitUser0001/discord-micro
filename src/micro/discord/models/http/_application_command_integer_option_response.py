# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_option_type import ApplicationCommandOptionType
from ._int53_type import Int53Type
from ._application_command_option_integer_choice_response import ApplicationCommandOptionIntegerChoiceResponse


class ApplicationCommandIntegerOptionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: ApplicationCommandOptionType
    name: str
    name_localized: str | None = None
    name_localizations: dict[str, Any] | None = None
    description: str
    description_localized: str | None = None
    description_localizations: dict[str, Any] | None = None
    required: bool | None = None
    autocomplete: bool | None = None
    choices: list[ApplicationCommandOptionIntegerChoiceResponse] | None = None
    min_value: Int53Type | None = None
    max_value: Int53Type | None = None
