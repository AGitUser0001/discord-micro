# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._afk_timeouts import AfkTimeouts
from ._available_locales_enum import AvailableLocalesEnum
from ._guild_explicit_content_filter_types import GuildExplicitContentFilterTypes
from ._guild_template_role_response import GuildTemplateRoleResponse
from ._snowflake_type import SnowflakeType
from ._user_notification_settings import UserNotificationSettings
from ._verification_levels import VerificationLevels
from ._guild_template_channel_response import GuildTemplateChannelResponse


class GuildTemplateSnapshotResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    description: str | None
    region: str | None
    verification_level: VerificationLevels
    default_message_notifications: UserNotificationSettings
    explicit_content_filter: GuildExplicitContentFilterTypes
    preferred_locale: AvailableLocalesEnum
    afk_channel_id: SnowflakeType | None
    afk_timeout: AfkTimeouts
    system_channel_id: SnowflakeType | None
    system_channel_flags: int
    roles: list[GuildTemplateRoleResponse]
    channels: list[GuildTemplateChannelResponse]
