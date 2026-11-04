# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_option_string_choice import ApplicationCommandOptionStringChoice


class InteractionApplicationCommandAutocompleteCallbackStringData(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    choices: Annotated[
        list[ApplicationCommandOptionStringChoice | None] | None, Field(max_length=25)
    ] = None
