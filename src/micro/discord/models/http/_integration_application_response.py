# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_types import ApplicationTypes
from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse


class IntegrationApplicationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    name: str
    icon: str | None
    description: str
    type: ApplicationTypes | None
    cover_image: str | None = None
    primary_sku_id: SnowflakeType | None = None
    flags: int
    flags_new: str
    bot: UserResponse | None = None
