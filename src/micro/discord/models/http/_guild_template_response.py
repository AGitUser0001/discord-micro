# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse
from ._guild_template_snapshot_response import GuildTemplateSnapshotResponse


class GuildTemplateResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    code: str
    name: str
    description: str | None
    usage_count: int
    creator_id: SnowflakeType
    creator: UserResponse | None
    created_at: AwareDatetime
    updated_at: AwareDatetime
    source_guild_id: SnowflakeType
    serialized_source_guild: GuildTemplateSnapshotResponse
    is_dirty: bool | None
