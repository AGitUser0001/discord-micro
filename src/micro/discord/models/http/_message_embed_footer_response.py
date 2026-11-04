# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class MessageEmbedFooterResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    text: str
    icon_url: str | None = None
    proxy_icon_url: AnyUrl | None = None
