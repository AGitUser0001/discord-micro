# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._unfurled_media_request import UnfurledMediaRequest


class ThumbnailComponentForMessageRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    description: Annotated[str | None, Field(max_length=1024, min_length=1)] = None
    spoiler: bool | None = None
    media: UnfurledMediaRequest
