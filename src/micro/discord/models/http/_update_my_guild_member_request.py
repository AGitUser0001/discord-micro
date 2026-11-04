# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class UpdateMyGuildMemberRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    nick: Annotated[str | None, Field(max_length=32)] = None
    avatar: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    bio: Annotated[str | None, Field(max_length=300)] = None
    banner: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
