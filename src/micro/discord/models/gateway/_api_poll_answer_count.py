# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIPollAnswerCount(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[float, Field(description='The `answer_id`')]
    count: Annotated[float, Field(description='The number of votes for this answer')]
    me_voted: Annotated[
        bool, Field(description='Whether the current user voted for this answer')
    ]
