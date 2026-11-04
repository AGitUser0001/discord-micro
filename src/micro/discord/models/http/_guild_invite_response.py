# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_liveliness_response import GuildLivelinessResponse
from ._invite_target_types import InviteTargetTypes
from ._invite_types import InviteTypes
from ._snowflake_type import SnowflakeType
from ._invite_channel_response import InviteChannelResponse
from ._invite_guild_response import InviteGuildResponse
from ._invite_guild_role_response import InviteGuildRoleResponse
from ._user_response import UserResponse
from ._invite_application_response import InviteApplicationResponse
from ._scheduled_event_response import ScheduledEventResponse


class GuildInviteResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: InviteTypes
    code: str
    inviter: UserResponse | None = None
    max_age: int | None = None
    created_at: AwareDatetime | None = None
    expires_at: AwareDatetime | None
    is_contact: bool | None = None
    flags: int | None = None
    guild: InviteGuildResponse
    guild_id: SnowflakeType
    channel: InviteChannelResponse
    target_type: InviteTargetTypes | None = None
    target_user: UserResponse | None = None
    target_application: InviteApplicationResponse | None = None
    guild_scheduled_event: ScheduledEventResponse | None = None
    target_channel_id: SnowflakeType | None = None
    target_message_id: SnowflakeType | None = None
    liveliness: GuildLivelinessResponse | None = None
    uses: int | None = None
    max_uses: int | None = None
    temporary: bool | None = None
    approximate_member_count: int | None = None
    approximate_presence_count: int | None = None
    is_nickname_changeable: bool | None = None
    roles: list[InviteGuildRoleResponse] | None = None
