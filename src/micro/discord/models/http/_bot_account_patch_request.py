# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class BotAccountPatchRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    username: Annotated[str, Field(max_length=32, min_length=2)]
    avatar: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    banner: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
