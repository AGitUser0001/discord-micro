# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIEmbedImage(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    url: Annotated[
        str,
        Field(
            description='Source url of image (only supports http(s) and attachments)'
        ),
    ]
    proxy_url: Annotated[
        str | None, Field(description='A proxied url of the image')
    ] = None
    height: Annotated[float | None, Field(description='Height of image')] = None
    width: Annotated[float | None, Field(description='Width of image')] = None
    content_type: Annotated[str | None, Field(description="The image's media type")] = (
        None
    )
    placeholder: Annotated[
        str | None, Field(description='ThumbHash placeholder of the image')
    ] = None
    placeholder_version: Annotated[
        float | None, Field(description='Version of the placeholder')
    ] = None
    description: Annotated[
        str | None, Field(description='Description (alt text) for the image')
    ] = None
    flags: Annotated[
        Literal[32] | None,
        Field(description='Embed media flags combined as a bitfield'),
    ] = None
