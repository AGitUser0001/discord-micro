# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayResumeData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    token: Annotated[str, Field(description='Session token')]
    session_id: Annotated[str, Field(description='Session id')]
    seq: Annotated[float, Field(description='Last sequence number received')]
