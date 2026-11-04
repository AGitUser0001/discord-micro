# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._unfurled_media_request import UnfurledMediaRequest


class MediaGalleryItemRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    description: Annotated[str | None, Field(max_length=1024, min_length=1)] = None
    spoiler: bool | None = None
    media: UnfurledMediaRequest
