# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._u_int32_type import UInt32Type


class MessageEmbedImageResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    url: str | None = None
    proxy_url: AnyUrl | None = None
    width: UInt32Type | None = None
    height: UInt32Type | None = None
    content_type: str | None = None
    placeholder: str | None = None
    placeholder_version: UInt32Type | None = None
    description: str | None = None
    flags: UInt32Type | None = None
