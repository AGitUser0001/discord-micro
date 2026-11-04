# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_command_permission import APIApplicationCommandPermission


class GatewayApplicationCommandPermissionsUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the command or the application ID')]
    application_id: Annotated[
        str, Field(description='ID of the application the command belongs to')
    ]
    guild_id: Annotated[str, Field(description='ID of the guild')]
    permissions: Annotated[
        list[APIApplicationCommandPermission],
        Field(description='Permissions for the command in the guild, max of 100'),
    ]
