# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class PollResultsEntryResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[int, Field(description='The answer_id')]
    count: Annotated[int, Field(description='The number of votes for this answer')]
    me_voted: Annotated[
        bool, Field(description='Whether the current user voted for this answer')
    ]
