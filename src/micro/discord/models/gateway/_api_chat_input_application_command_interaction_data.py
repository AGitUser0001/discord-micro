# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_command_interaction_data_option_interaction_type_application_command import APIApplicationCommandInteractionDataOptionInteractionTypeApplicationCommand
from ._api_interaction_data_resolved import APIInteractionDataResolved


class APIChatInputApplicationCommandInteractionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: str
    type: Annotated[
        Literal[1],
        Field(
            description='Slash commands; a text-based command that shows up when a user types `/`'
        ),
    ]
    name: str
    guild_id: str | None = None
    options: (
        list[
            APIApplicationCommandInteractionDataOptionInteractionTypeApplicationCommand
        ]
        | None
    ) = None
    resolved: APIInteractionDataResolved | None = None
