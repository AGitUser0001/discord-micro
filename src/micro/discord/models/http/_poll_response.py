# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._poll_layout_types import PollLayoutTypes
from ._poll_results_response import PollResultsResponse
from ._poll_media_response import PollMediaResponse
from ._poll_answer_response import PollAnswerResponse


class PollResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    question: Annotated[
        PollMediaResponse,
        Field(description='The question of the poll. Only `text` is supported.'),
    ]
    answers: Annotated[
        list[PollAnswerResponse],
        Field(description='Each of the answers available in the poll'),
    ]
    expiry: Annotated[AwareDatetime, Field(description='The time when the poll ends')]
    allow_multiselect: Annotated[
        bool, Field(description='Whether a user can select multiple answers')
    ]
    layout_type: Annotated[
        PollLayoutTypes, Field(description='The layout type of the poll')
    ]
    results: Annotated[
        PollResultsResponse, Field(description='The results of the poll')
    ]
