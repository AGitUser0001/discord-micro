# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_resume_data import GatewayResumeData


class GatewayResume(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    op: Annotated[
        Literal[6], Field(description='Resume a previous session that was disconnected')
    ]
    d: GatewayResumeData
