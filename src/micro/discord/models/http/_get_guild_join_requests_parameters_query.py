# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_join_request_application_status import GuildJoinRequestApplicationStatus
from ._snowflake_type import SnowflakeType


class GetGuildJoinRequestsParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    status: GuildJoinRequestApplicationStatus | None = None
    limit: Annotated[int | None, Field(ge=1, le=100)] = None
    before: SnowflakeType | None = None
    after: SnowflakeType | None = None
