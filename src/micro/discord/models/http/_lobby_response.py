# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._u_int32_type import UInt32Type
from ._guild_channel_response import GuildChannelResponse
from ._lobby_member_response import LobbyMemberResponse


class LobbyResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    application_id: SnowflakeType
    metadata: dict[str, Any] | None
    members: list[LobbyMemberResponse]
    linked_channel: GuildChannelResponse | None = None
    flags: UInt32Type
    override_event_webhooks_url: str | None = None
