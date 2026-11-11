# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_user import APIUser


class GatewayGuildBanModifyDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='ID of the guild')]
    user: Annotated[APIUser, Field(description='The banned user')]
