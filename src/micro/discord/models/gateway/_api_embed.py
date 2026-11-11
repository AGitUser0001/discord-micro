# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type9 import Type9
from ._flags40 import Flags40
from ._api_embed_footer import APIEmbedFooter
from ._api_embed_image import APIEmbedImage
from ._api_embed_video import APIEmbedVideo
from ._api_embed_provider import APIEmbedProvider
from ._api_embed_author import APIEmbedAuthor
from ._api_embed_field import APIEmbedField
from ._api_component_embed_container import APIComponentEmbedContainer


class APIEmbed(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    title: Annotated[
        str | None, Field(description='Title of embed\n\nLength limit: 256 characters')
    ] = None
    type: Annotated[
        Type9 | None,
        Field(description='Type of embed (always "rich" for webhook embeds)'),
    ] = None
    description: Annotated[
        str | None,
        Field(description='Description of embed\n\nLength limit: 4096 characters'),
    ] = None
    url: Annotated[str | None, Field(description='URL of embed')] = None
    timestamp: Annotated[
        str | None, Field(description='Timestamp of embed content')
    ] = None
    color: Annotated[float | None, Field(description='Color code of the embed')] = None
    footer: Annotated[
        APIEmbedFooter | None, Field(description='Footer information')
    ] = None
    image: Annotated[APIEmbedImage | None, Field(description='Image information')] = (
        None
    )
    thumbnail: Annotated[
        APIEmbedImage | None, Field(description='Thumbnail information')
    ] = None
    video: Annotated[APIEmbedVideo | None, Field(description='Video information')] = (
        None
    )
    provider: Annotated[
        APIEmbedProvider | None, Field(description='Provider information')
    ] = None
    author: Annotated[
        APIEmbedAuthor | None, Field(description='Author information')
    ] = None
    fields: Annotated[
        list[APIEmbedField] | None,
        Field(description='Fields information\n\nLength limit: 25 field objects'),
    ] = None
    components: Annotated[
        list[APIComponentEmbedContainer] | None,
        Field(
            description='Components that make up the embed, only present on `components` type embeds.'
        ),
    ] = None
    flags: Annotated[
        Flags40 | None, Field(description='Embed flags combined as a bitfield')
    ] = None
