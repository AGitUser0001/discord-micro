# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_poll_media import APIPollMedia
from ._api_poll_answer import APIPollAnswer
from ._api_poll_results import APIPollResults


class APIPoll(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    question: Annotated[APIPollMedia, Field(description='The question of the poll')]
    allow_multiselect: Annotated[
        bool, Field(description='Whether a user can select multiple answers')
    ]
    layout_type: Annotated[Literal[1], Field(description='The layout type of the poll')]
    answers: Annotated[
        list[APIPollAnswer],
        Field(description='Each of the answers available in the poll, up to 10'),
    ]
    expiry: Annotated[
        str | None, Field(description='The time when the poll ends (IS08601 timestamp)')
    ]
    results: Annotated[
        APIPollResults | None, Field(description='The results of the poll')
    ] = None
