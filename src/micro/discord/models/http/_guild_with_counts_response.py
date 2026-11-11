# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._afk_timeouts import AfkTimeouts
from ._available_locales_enum import AvailableLocalesEnum
from ._guild_explicit_content_filter_types import GuildExplicitContentFilterTypes
from ._guild_features import GuildFeatures
from ._guild_incidents_data_response import GuildIncidentsDataResponse
from ._guild_mfa_level import GuildMFALevel
from ._guild_nsfw_content_level import GuildNSFWContentLevel
from ._premium_guild_tiers import PremiumGuildTiers
from ._snowflake_type import SnowflakeType
from ._user_notification_settings import UserNotificationSettings
from ._verification_levels import VerificationLevels
from ._emoji_response import EmojiResponse
from ._guild_role_response import GuildRoleResponse
from ._guild_sticker_response import GuildStickerResponse


class GuildWithCountsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    icon: str | None
    description: str | None
    home_header: str | None
    splash: str | None
    discovery_splash: str | None
    features: list[GuildFeatures]
    banner: str | None
    owner_id: SnowflakeType
    application_id: SnowflakeType | None
    region: str
    afk_channel_id: SnowflakeType | None
    afk_timeout: AfkTimeouts
    system_channel_id: SnowflakeType | None
    system_channel_flags: int
    widget_enabled: bool
    widget_channel_id: SnowflakeType | None
    verification_level: VerificationLevels
    roles: list[GuildRoleResponse]
    default_message_notifications: UserNotificationSettings
    mfa_level: GuildMFALevel
    explicit_content_filter: GuildExplicitContentFilterTypes
    max_presences: int | None
    max_members: int
    max_stage_video_channel_users: int
    max_video_channel_users: int
    vanity_url_code: str | None
    premium_tier: PremiumGuildTiers
    premium_subscription_count: int
    preferred_locale: AvailableLocalesEnum
    rules_channel_id: SnowflakeType | None
    safety_alerts_channel_id: SnowflakeType | None
    public_updates_channel_id: SnowflakeType | None
    premium_progress_bar_enabled: bool
    premium_progress_bar_enabled_user_updated_at: AwareDatetime | None = None
    nsfw: bool
    nsfw_level: GuildNSFWContentLevel
    emojis: list[EmojiResponse]
    stickers: list[GuildStickerResponse]
    incidents_data: GuildIncidentsDataResponse | None
    approximate_member_count: int | None = None
    approximate_presence_count: int | None = None
