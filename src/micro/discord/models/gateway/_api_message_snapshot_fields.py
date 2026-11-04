# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_sticker_item import APIStickerItem
from ._type15 import Type15
from ._flags54 import Flags54
from ._api_embed import APIEmbed
from ._api_user import APIUser
from ._api_sticker import APISticker
from ._api_attachment import APIAttachment
from ._api_message_top_level_component import APIMessageTopLevelComponent


class APIMessageSnapshotFields(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    mentions: Annotated[
        list[APIUser],
        Field(
            description='Users specifically mentioned in the message\n\nThe `member` field is only present in `MESSAGE_CREATE` and `MESSAGE_UPDATE` events\nfrom text-based guild channels'
        ),
    ]
    content: Annotated[
        str,
        Field(
            description='Contents of the message\n\nThe `MESSAGE_CONTENT` privileged gateway intent is required for verified applications to receive a non-empty value from this field\n\nIn the Discord Developers Portal, you need to enable the toggle of this intent of your application in **Bot \\> Privileged Gateway Intents**.\nYou also need to specify the intent bit value (`1 << 15`) if you are connecting to the gateway'
        ),
    ]
    timestamp: Annotated[str, Field(description='When this message was sent')]
    edited_timestamp: Annotated[
        str | None, Field(description='When this message was edited (or null if never)')
    ]
    mention_roles: Annotated[
        list[str], Field(description='Roles specifically mentioned in this message')
    ]
    attachments: Annotated[
        list[APIAttachment],
        Field(
            description='Any attached files that are not referenced in embeds or components'
        ),
    ]
    embeds: Annotated[list[APIEmbed], Field(description='Any embedded content')]
    type: Annotated[Type15, Field(description='Type of message')]
    flags: Annotated[
        Flags54 | None, Field(description='Message flags combined as a bitfield')
    ] = None
    components: Annotated[
        list[APIMessageTopLevelComponent] | None,
        Field(
            description='Sent if the message contains components like buttons, action rows, or other interactive components\n\nThe `MESSAGE_CONTENT` privileged gateway intent is required for verified applications to receive a non-empty value from this field\n\nIn the Discord Developers Portal, you need to enable the toggle of this intent of your application in **Bot \\> Privileged Gateway Intents**.\nYou also need to specify the intent bit value (`1 << 15`) if you are connecting to the gateway'
        ),
    ] = None
    sticker_items: Annotated[
        list[APIStickerItem] | None,
        Field(description='Sent if the message contains stickers'),
    ] = None
    stickers: Annotated[
        list[APISticker] | None,
        Field(deprecated=True, description='The stickers sent with the message'),
    ] = None
