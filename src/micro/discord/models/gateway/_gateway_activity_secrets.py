# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayActivitySecrets(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    join: Annotated[str | None, Field(description='The secret for joining a party')] = (
        None
    )
    spectate: Annotated[
        str | None, Field(description='The secret for spectating a game')
    ] = None
    match: Annotated[
        str | None, Field(description='The secret for a specific instance of a match')
    ] = None
