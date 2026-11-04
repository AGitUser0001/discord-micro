# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._poll_results_entry_response import PollResultsEntryResponse


class PollResultsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    answer_counts: Annotated[
        list[PollResultsEntryResponse], Field(description='The counts for each answer')
    ]
    is_finalized: Annotated[
        bool, Field(description='Whether the votes have been precisely counted')
    ]
