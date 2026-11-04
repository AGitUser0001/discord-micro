# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIPrimaryEntryPointCommandInteractionData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: str
    type: Annotated[
        Literal[4],
        Field(
            description="A UI-based command that represents the primary way to invoke an app's Activity"
        ),
    ]
    name: str
    guild_id: str | None = None
