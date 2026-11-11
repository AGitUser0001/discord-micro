# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_type import MessageType
from ._separator_component_response import SeparatorComponentResponse
from ._snowflake_type import SnowflakeType
from ._text_display_component_response import TextDisplayComponentResponse
from ._file_component_response import FileComponentResponse
from ._message_sticker_item_response import MessageStickerItemResponse
from ._standard_sticker_response import StandardStickerResponse
from ._user_response import UserResponse
from ._guild_sticker_response import GuildStickerResponse
from ._media_gallery_component_response import MediaGalleryComponentResponse
from ._message_attachment_response import MessageAttachmentResponse
from ._section_component_response import SectionComponentResponse
from ._action_row_component_response import ActionRowComponentResponse
from ._container_component_response import ContainerComponentResponse
from ._message_embed_response import MessageEmbedResponse


class MinimalContentMessageResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageType
    content: str
    mentions: list[UserResponse]
    mention_roles: list[SnowflakeType]
    attachments: list[MessageAttachmentResponse]
    embeds: list[MessageEmbedResponse]
    timestamp: AwareDatetime
    edited_timestamp: AwareDatetime | None
    flags: int
    components: list[
        ActionRowComponentResponse
        | ContainerComponentResponse
        | FileComponentResponse
        | MediaGalleryComponentResponse
        | SectionComponentResponse
        | SeparatorComponentResponse
        | TextDisplayComponentResponse
    ]
    stickers: list[GuildStickerResponse | StandardStickerResponse] | None = None
    sticker_items: list[MessageStickerItemResponse] | None = None
