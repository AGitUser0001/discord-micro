# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_option_type import ApplicationCommandOptionType
from ._int53_type import Int53Type
from ._application_command_option_integer_choice import ApplicationCommandOptionIntegerChoice


class ApplicationCommandIntegerOption(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: ApplicationCommandOptionType
    name: Annotated[str, Field(max_length=32, min_length=1)]
    name_localizations: dict[str, Any] | None = None
    description: Annotated[str, Field(max_length=100, min_length=1)]
    description_localizations: dict[str, Any] | None = None
    required: bool | None = None
    autocomplete: bool | None = None
    choices: Annotated[
        list[ApplicationCommandOptionIntegerChoice] | None, Field(max_length=25)
    ] = None
    min_value: Int53Type | None = None
    max_value: Int53Type | None = None
