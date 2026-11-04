# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_reaction_count_details_response import MessageReactionCountDetailsResponse
from ._message_reaction_emoji_response import MessageReactionEmojiResponse


class MessageReactionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    emoji: MessageReactionEmojiResponse
    count: int
    count_details: MessageReactionCountDetailsResponse
    burst_colors: list[str]
    me_burst: bool
    me: bool
