# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_command_interaction_data_basic_option_interaction_type_application_command import APIApplicationCommandInteractionDataBasicOptionInteractionTypeApplicationCommand


class APIApplicationCommandInteractionDataSubcommandOptionApplicationCommand(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    type: Literal[1]
    options: (
        list[
            APIApplicationCommandInteractionDataBasicOptionInteractionTypeApplicationCommand
        ]
        | None
    ) = None
