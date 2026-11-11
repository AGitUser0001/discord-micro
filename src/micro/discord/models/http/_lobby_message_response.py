# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_lobby_member_response import MessageLobbyMemberResponse
from ._message_type import MessageType
from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse


class LobbyMessageResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: MessageType
    content: str
    lobby_id: SnowflakeType
    channel_id: SnowflakeType
    author: UserResponse
    lobby_member: MessageLobbyMemberResponse | None = None
    metadata: dict[str, str] | None = None
    moderation_metadata: dict[str, str] | None = None
    flags: int
    application_id: SnowflakeType | None = None
