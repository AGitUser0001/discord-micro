# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_message_application_command_interaction_data_resolved import APIMessageApplicationCommandInteractionDataResolved


class APIMessageApplicationCommandInteractionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: str
    type: Annotated[
        Literal[3],
        Field(
            description='A UI-based command that shows up when you right click or tap on a message'
        ),
    ]
    name: str
    guild_id: str | None = None
    target_id: str
    resolved: APIMessageApplicationCommandInteractionDataResolved
