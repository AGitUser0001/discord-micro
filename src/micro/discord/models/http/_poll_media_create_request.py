# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._poll_emoji_create_request import PollEmojiCreateRequest


class PollMediaCreateRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    text: Annotated[
        str | None,
        Field(description='The text of the field', max_length=300, min_length=1),
    ] = None
    emoji: Annotated[
        PollEmojiCreateRequest | None, Field(description='The emoji of the field')
    ] = None
