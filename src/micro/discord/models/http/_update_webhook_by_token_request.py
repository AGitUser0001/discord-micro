# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class UpdateWebhookByTokenRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str | None, Field(max_length=80, min_length=1)] = None
    avatar: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
