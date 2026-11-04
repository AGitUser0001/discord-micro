# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._separator_component_for_message_request import SeparatorComponentForMessageRequest
from ._text_display_component_for_message_request import TextDisplayComponentForMessageRequest
from ._file_component_for_message_request import FileComponentForMessageRequest
from ._message_allowed_mentions_request import MessageAllowedMentionsRequest
from ._message_attachment_request import MessageAttachmentRequest
from ._rich_embed import RichEmbed
from ._media_gallery_component_for_message_request import MediaGalleryComponentForMessageRequest
from ._poll_create_request import PollCreateRequest
from ._section_component_for_message_request import SectionComponentForMessageRequest
from ._action_row_component_for_message_request import ActionRowComponentForMessageRequest
from ._container_component_for_message_request import ContainerComponentForMessageRequest


class IncomingWebhookUpdateRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    content: Annotated[str | None, Field(max_length=2000)] = None
    embeds: Annotated[list[RichEmbed] | None, Field(max_length=10)] = None
    allowed_mentions: MessageAllowedMentionsRequest | None = None
    components: Annotated[
        list[
            ActionRowComponentForMessageRequest
            | ContainerComponentForMessageRequest
            | FileComponentForMessageRequest
            | MediaGalleryComponentForMessageRequest
            | SectionComponentForMessageRequest
            | SeparatorComponentForMessageRequest
            | TextDisplayComponentForMessageRequest
        ]
        | None,
        Field(max_length=40),
    ] = None
    attachments: Annotated[
        list[MessageAttachmentRequest] | None, Field(max_length=10)
    ] = None
    poll: PollCreateRequest | None = None
    flags: int | None = None
