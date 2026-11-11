# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class RichEmbedImage(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    url: AnyUrl | None = None
    width: int | None = None
    height: int | None = None
    placeholder: Annotated[str | None, Field(max_length=64)] = None
    placeholder_version: Annotated[int | None, Field(ge=0, le=2147483647)] = None
    is_animated: bool | None = None
    description: Annotated[str | None, Field(max_length=4096)] = None
