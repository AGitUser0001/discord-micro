# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayInvalidSession(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[9],
        Field(
            description='The session has been invalidated. You should reconnect and identify/resume accordingly'
        ),
    ]
    d: bool
    t: None
    s: None
