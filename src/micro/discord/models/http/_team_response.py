# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._team_member_response import TeamMemberResponse


class TeamResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    icon: str | None
    name: str
    owner_user_id: SnowflakeType
    members: list[TeamMemberResponse]
