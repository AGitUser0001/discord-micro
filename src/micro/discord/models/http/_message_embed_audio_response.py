# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class MessageEmbedAudioResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    url: str | None = None
    proxy_url: AnyUrl | None = None
    content_type: str | None = None
    description: str | None = None
