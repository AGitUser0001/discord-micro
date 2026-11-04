# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class MessageEmbedFieldResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    value: str
    inline: bool
