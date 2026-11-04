# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._invite_target_types import InviteTargetTypes
from ._snowflake_type import SnowflakeType
from ._role_ids import RoleIds


class CreateGuildInviteRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    max_age: Annotated[int | None, Field(ge=0, le=5184000)] = None
    temporary: bool | None = None
    max_uses: Annotated[int | None, Field(ge=0, le=100)] = None
    unique: bool | None = None
    target_user_id: SnowflakeType | None = None
    target_application_id: SnowflakeType | None = None
    target_type: InviteTargetTypes | None = None
    role_ids: str | RoleIds | None = None
