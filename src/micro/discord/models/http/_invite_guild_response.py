# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_features import GuildFeatures
from ._guild_nsfw_content_level import GuildNSFWContentLevel
from ._snowflake_type import SnowflakeType
from ._verification_levels import VerificationLevels


class InviteGuildResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    splash: str | None
    banner: str | None
    description: str | None
    icon: str | None
    features: list[GuildFeatures]
    verification_level: VerificationLevels | None
    vanity_url_code: str | None
    nsfw_level: GuildNSFWContentLevel | None
    nsfw: bool | None
    premium_subscription_count: int
