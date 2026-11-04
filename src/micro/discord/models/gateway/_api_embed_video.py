# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIEmbedVideo(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    url: Annotated[str | None, Field(description='Source url of video')] = None
    proxy_url: Annotated[
        str | None, Field(description='A proxied url of the video')
    ] = None
    height: Annotated[float | None, Field(description='Height of video')] = None
    width: Annotated[float | None, Field(description='Width of video')] = None
    content_type: Annotated[str | None, Field(description="The video's media type")] = (
        None
    )
    placeholder: Annotated[
        str | None, Field(description='ThumbHash placeholder of the video')
    ] = None
    placeholder_version: Annotated[
        float | None, Field(description='Version of the placeholder')
    ] = None
    description: Annotated[
        str | None, Field(description='Description (alt text) for the video')
    ] = None
    flags: Annotated[
        Literal[32] | None,
        Field(description='Embed media flags combined as a bitfield'),
    ] = None
