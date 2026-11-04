# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_sticker import APISticker


class GatewayGuildStickersUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='ID of the guild')]
    stickers: Annotated[list[APISticker], Field(description='Array of stickers')]
