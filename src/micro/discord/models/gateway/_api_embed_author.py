# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIEmbedAuthor(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[
        str, Field(description='Name of author\n\nLength limit: 256 characters')
    ]
    url: Annotated[str | None, Field(description='URL of author')] = None
    icon_url: Annotated[
        str | None,
        Field(description='URL of author icon (only supports http(s) and attachments)'),
    ] = None
    proxy_icon_url: Annotated[
        str | None, Field(description='A proxied url of author icon')
    ] = None
