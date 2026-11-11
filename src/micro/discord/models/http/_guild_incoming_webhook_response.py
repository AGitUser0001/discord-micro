# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._webhook_types import WebhookTypes
from ._user_response import UserResponse


class GuildIncomingWebhookResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    application_id: SnowflakeType | None
    avatar: str | None
    channel_id: SnowflakeType | None
    guild_id: SnowflakeType | None = None
    id: SnowflakeType
    name: str
    type: WebhookTypes
    user: UserResponse | None = None
    token: str | None = None
    url: AnyUrl | None = None
