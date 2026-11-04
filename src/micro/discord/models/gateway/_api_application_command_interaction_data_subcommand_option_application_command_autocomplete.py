# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_command_interaction_data_basic_option_interaction_type_application_command_autocomplete import APIApplicationCommandInteractionDataBasicOptionInteractionTypeApplicationCommandAutocomplete


class APIApplicationCommandInteractionDataSubcommandOptionApplicationCommandAutocomplete(
    BaseModel
):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    type: Literal[1]
    options: (
        list[
            APIApplicationCommandInteractionDataBasicOptionInteractionTypeApplicationCommandAutocomplete
        ]
        | None
    ) = None
