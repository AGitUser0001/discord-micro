# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._afk_timeouts import AfkTimeouts
from ._available_locales_enum import AvailableLocalesEnum
from ._guild_explicit_content_filter_types import GuildExplicitContentFilterTypes
from ._feature import Feature
from ._snowflake_type import SnowflakeType
from ._user_notification_settings import UserNotificationSettings
from ._verification_levels import VerificationLevels


class GuildPatchRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str | None, Field(max_length=100, min_length=2)] = None
    description: Annotated[str | None, Field(max_length=300, min_length=0)] = None
    region: str | None = None
    icon: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    verification_level: VerificationLevels | None = None
    default_message_notifications: UserNotificationSettings | None = None
    explicit_content_filter: GuildExplicitContentFilterTypes | None = None
    preferred_locale: AvailableLocalesEnum | None = None
    afk_timeout: AfkTimeouts | None = None
    afk_channel_id: SnowflakeType | None = None
    system_channel_id: SnowflakeType | None = None
    splash: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    banner: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    system_channel_flags: int | None = None
    features: Annotated[list[Feature | None] | None, Field(max_length=1521)] = None
    discovery_splash: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    home_header: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    rules_channel_id: SnowflakeType | None = None
    safety_alerts_channel_id: SnowflakeType | None = None
    public_updates_channel_id: SnowflakeType | None = None
    premium_progress_bar_enabled: bool | None = None
