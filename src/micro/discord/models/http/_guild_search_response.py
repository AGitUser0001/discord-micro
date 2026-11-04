# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._thread_member_response import ThreadMemberResponse
from ._thread_response import ThreadResponse
from ._search_message_response import SearchMessageResponse


class GuildSearchResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    messages: list[list[SearchMessageResponse]]
    doing_deep_historical_index: bool
    total_results: int
    threads: list[ThreadResponse] | None = None
    members: list[ThreadMemberResponse] | None = None
    documents_indexed: int | None = None
