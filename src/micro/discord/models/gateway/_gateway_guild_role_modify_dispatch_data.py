# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_role import APIRole


class GatewayGuildRoleModifyDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='The id of the guild')]
    role: Annotated[APIRole, Field(description='The role created or updated')]
