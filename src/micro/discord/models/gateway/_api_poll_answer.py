# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_poll_media import APIPollMedia


class APIPollAnswer(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    poll_media: Annotated[APIPollMedia, Field(description='The data of the answer')]
    answer_id: Annotated[
        float,
        Field(
            description='The ID of the answer. Starts at `1` for the first answer and goes up sequentially'
        ),
    ]
