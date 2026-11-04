# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._guild_member_response import GuildMemberResponse


class VoiceStateResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: SnowflakeType | None
    deaf: bool
    guild_id: SnowflakeType | None
    member: GuildMemberResponse | None = None
    mute: bool
    request_to_speak_timestamp: AwareDatetime | None
    suppress: bool
    self_stream: bool | None
    self_deaf: bool
    self_mute: bool
    self_video: bool
    session_id: str
    user_id: SnowflakeType
