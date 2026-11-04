# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_embed_author_response import MessageEmbedAuthorResponse
from ._message_embed_field_response import MessageEmbedFieldResponse
from ._message_embed_footer_response import MessageEmbedFooterResponse
from ._message_embed_provider_response import MessageEmbedProviderResponse
from ._message_embed_image_response import MessageEmbedImageResponse
from ._message_embed_video_response import MessageEmbedVideoResponse
from ._container_component_response import ContainerComponentResponse


class MessageEmbedResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: str
    url: AnyUrl | None = None
    title: str | None = None
    description: str | None = None
    color: int | None = None
    timestamp: AwareDatetime | None = None
    fields: list[MessageEmbedFieldResponse] | None = None
    author: MessageEmbedAuthorResponse | None = None
    provider: MessageEmbedProviderResponse | None = None
    image: MessageEmbedImageResponse | None = None
    thumbnail: MessageEmbedImageResponse | None = None
    video: MessageEmbedVideoResponse | None = None
    footer: MessageEmbedFooterResponse | None = None
    flags: int | None = None
    components: list[ContainerComponentResponse] | None = None
