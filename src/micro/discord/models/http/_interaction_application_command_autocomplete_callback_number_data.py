# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_option_number_choice import ApplicationCommandOptionNumberChoice


class InteractionApplicationCommandAutocompleteCallbackNumberData(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    choices: Annotated[
        list[ApplicationCommandOptionNumberChoice | None] | None, Field(max_length=25)
    ] = None
