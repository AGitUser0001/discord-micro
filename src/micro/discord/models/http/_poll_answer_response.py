# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._poll_media_response import PollMediaResponse


class PollAnswerResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    answer_id: Annotated[int, Field(description='The ID of the answer')]
    poll_media: Annotated[
        PollMediaResponse, Field(description='The data of the answer')
    ]
