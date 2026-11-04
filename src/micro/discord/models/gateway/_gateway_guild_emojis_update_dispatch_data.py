# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_emoji import APIEmoji


class GatewayGuildEmojisUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='ID of the guild')]
    emojis: Annotated[list[APIEmoji], Field(description='Array of emojis')]
