# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._poll_layout_types import PollLayoutTypes
from ._poll_media import PollMedia
from ._poll_answer_create_request import PollAnswerCreateRequest


class PollCreateRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    question: Annotated[
        PollMedia,
        Field(description='The question of the poll. Only `text` is supported.'),
    ]
    answers: Annotated[
        list[PollAnswerCreateRequest],
        Field(
            description='Each of the answers available in the poll, up to 10',
            max_length=10,
            min_length=1,
        ),
    ]
    allow_multiselect: Annotated[
        bool | None, Field(description='Whether a user can select multiple answers')
    ] = None
    layout_type: Annotated[
        PollLayoutTypes | None,
        Field(description='The layout type of the poll. Defaults to... DEFAULT!'),
    ] = None
    duration: Annotated[
        int | None,
        Field(
            description='Number of hours the poll should be open for, up to 32 days. Defaults to 24',
            ge=1,
            le=768,
        ),
    ] = None
