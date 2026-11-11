# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._poll_media_create_request import PollMediaCreateRequest


class PollAnswerCreateRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    poll_media: Annotated[
        PollMediaCreateRequest, Field(description='The data of the answer')
    ]
