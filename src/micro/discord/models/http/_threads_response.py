# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._thread_member_response import ThreadMemberResponse
from ._thread_response import ThreadResponse
from ._message_response import MessageResponse


class ThreadsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    threads: list[ThreadResponse]
    members: list[ThreadMemberResponse]
    has_more: bool
    first_messages: list[MessageResponse] | None = None
