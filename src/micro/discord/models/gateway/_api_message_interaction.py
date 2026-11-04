# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type12 import Type12
from ._partial_api_message_interaction_guild_member import PartialAPIMessageInteractionGuildMember
from ._api_user import APIUser


class APIMessageInteraction(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the interaction')]
    type: Annotated[Type12, Field(description='The type of interaction')]
    name: Annotated[
        str,
        Field(
            description='The name of the application command, including subcommands and subcommand groups'
        ),
    ]
    user: Annotated[APIUser, Field(description='The user who invoked the interaction')]
    member: Annotated[
        PartialAPIMessageInteractionGuildMember | None,
        Field(
            description='The guild member who invoked the interaction, only sent in MESSAGE_CREATE events'
        ),
    ] = None
