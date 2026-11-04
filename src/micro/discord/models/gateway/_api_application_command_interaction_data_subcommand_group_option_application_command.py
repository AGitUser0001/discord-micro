# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_command_interaction_data_subcommand_option_application_command import APIApplicationCommandInteractionDataSubcommandOptionApplicationCommand


class APIApplicationCommandInteractionDataSubcommandGroupOptionApplicationCommand(
    BaseModel
):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    type: Literal[2]
    options: list[
        APIApplicationCommandInteractionDataSubcommandOptionApplicationCommand
    ]
