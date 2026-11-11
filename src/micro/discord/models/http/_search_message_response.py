# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_activity_response import MessageActivityResponse
from ._message_lobby_member_response import MessageLobbyMemberResponse
from ._message_type import MessageType
from ._resolved_objects_response import ResolvedObjectsResponse
from ._nonce8 import Nonce8
from ._nonce9 import Nonce9
from ._separator_component_response import SeparatorComponentResponse
from ._snowflake_type import SnowflakeType
from ._text_display_component_response import TextDisplayComponentResponse
from ._custom_client_theme_response import CustomClientThemeResponse
from ._file_component_response import FileComponentResponse
from ._message_call_response import MessageCallResponse
from ._message_mention_channel_response import MessageMentionChannelResponse
from ._message_reaction_response import MessageReactionResponse
from ._message_reference_response import MessageReferenceResponse
from ._message_role_subscription_data_response import MessageRoleSubscriptionDataResponse
from ._message_sticker_item_response import MessageStickerItemResponse
from ._purchase_notification_response import PurchaseNotificationResponse
from ._standard_sticker_response import StandardStickerResponse
from ._user_response import UserResponse
from ._application_command_interaction_metadata_response import ApplicationCommandInteractionMetadataResponse
from ._basic_application_response_with_bot import BasicApplicationResponseWithBot
from ._guild_sticker_response import GuildStickerResponse
from ._media_gallery_component_response import MediaGalleryComponentResponse
from ._message_attachment_response import MessageAttachmentResponse
from ._message_component_interaction_metadata_response import MessageComponentInteractionMetadataResponse
from ._message_interaction_response import MessageInteractionResponse
from ._modal_submit_interaction_metadata_response import ModalSubmitInteractionMetadataResponse
from ._poll_response import PollResponse
from ._section_component_response import SectionComponentResponse
from ._thread_response import ThreadResponse
from ._action_row_component_response import ActionRowComponentResponse
from ._container_component_response import ContainerComponentResponse
from ._message_embed_response import MessageEmbedResponse
from ._message_snapshot_response import MessageSnapshotResponse
from ._basic_message_response import BasicMessageResponse


class SearchMessageResponse(DiscordModel):
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
    id: SnowflakeType
    channel_id: SnowflakeType
    author: UserResponse
    pinned: bool
    mention_everyone: bool
    tts: bool
    call: MessageCallResponse | None = None
    activity: MessageActivityResponse | None = None
    application: BasicApplicationResponseWithBot | None = None
    application_id: SnowflakeType | None = None
    interaction: MessageInteractionResponse | None = None
    nonce: Nonce8 | Nonce9 | None = None
    webhook_id: SnowflakeType | None = None
    message_reference: MessageReferenceResponse | None = None
    thread: ThreadResponse | None = None
    mention_channels: list[MessageMentionChannelResponse] | None = None
    role_subscription_data: MessageRoleSubscriptionDataResponse | None = None
    purchase_notification: PurchaseNotificationResponse | None = None
    position: int | None = None
    resolved: ResolvedObjectsResponse | None = None
    poll: PollResponse | None = None
    shared_client_theme: CustomClientThemeResponse | None = None
    interaction_metadata: (
        ApplicationCommandInteractionMetadataResponse
        | MessageComponentInteractionMetadataResponse
        | ModalSubmitInteractionMetadataResponse
        | None
    ) = None
    message_snapshots: list[MessageSnapshotResponse] | None = None
    lobby_member: MessageLobbyMemberResponse | None = None
    actor: UserResponse | None = None
    reactions: list[MessageReactionResponse] | None = None
    referenced_message: BasicMessageResponse | None = None
    hit: bool
    restriction_count: int | None = None
    author_restriction_count: int | None = None
    source_author_restriction_count: int | None = None
    forward_source_author_id: SnowflakeType | None = None
