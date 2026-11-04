# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._rich_embed_author import RichEmbedAuthor
from ._rich_embed_field import RichEmbedField
from ._rich_embed_footer import RichEmbedFooter
from ._rich_embed_image import RichEmbedImage
from ._rich_embed_provider import RichEmbedProvider
from ._rich_embed_thumbnail import RichEmbedThumbnail
from ._rich_embed_video import RichEmbedVideo


class RichEmbed(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[str | None, Field(max_length=152133)] = None
    url: AnyUrl | None = None
    title: Annotated[str | None, Field(max_length=256)] = None
    color: Annotated[int | None, Field(ge=0, le=16777215)] = None
    timestamp: AwareDatetime | None = None
    description: Annotated[str | None, Field(max_length=4096)] = None
    author: RichEmbedAuthor | None = None
    image: RichEmbedImage | None = None
    thumbnail: RichEmbedThumbnail | None = None
    footer: RichEmbedFooter | None = None
    fields: Annotated[list[RichEmbedField] | None, Field(max_length=25)] = None
    provider: RichEmbedProvider | None = None
    video: RichEmbedVideo | None = None
