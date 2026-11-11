# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_poll_answer_count import APIPollAnswerCount


class APIPollResults(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    is_finalized: Annotated[
        bool, Field(description='Whether the votes have been precisely counted')
    ]
    answer_counts: Annotated[
        list[APIPollAnswerCount], Field(description='The counts for each answer')
    ]
