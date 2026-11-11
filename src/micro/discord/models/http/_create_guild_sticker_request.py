# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class CreateGuildStickerRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(max_length=30, min_length=2)]
    tags: Annotated[str, Field(max_length=200, min_length=1)]
    description: Annotated[str | None, Field(max_length=100)] = None
    file: bytes
