# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIEmbedFooter(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    text: Annotated[
        str, Field(description='Footer text\n\nLength limit: 2048 characters')
    ]
    icon_url: Annotated[
        str | None,
        Field(description='URL of footer icon (only supports http(s) and attachments)'),
    ] = None
    proxy_icon_url: Annotated[
        str | None, Field(description='A proxied url of footer icon')
    ] = None
