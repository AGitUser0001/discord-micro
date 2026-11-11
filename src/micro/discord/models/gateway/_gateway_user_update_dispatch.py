# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_user import APIUser


class GatewayUserUpdateDispatch(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    s: Annotated[
        float,
        Field(description='Sequence number, used for resuming sessions and heartbeats'),
    ]
    op: Annotated[Literal[0], Field(description='An event was dispatched')]
    t: Literal['USER_UPDATE']
    d: APIUser
