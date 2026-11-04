# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class GuildRoleTagsResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    premium_subscriber: Annotated[None, Field(None)] = None
    bot_id: SnowflakeType | None = None
    integration_id: SnowflakeType | None = None
    subscription_listing_id: SnowflakeType | None = None
    available_for_purchase: Annotated[None, Field(None)] = None
    guild_connections: Annotated[None, Field(None)] = None
