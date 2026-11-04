# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType


class UserAvatarDecorationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    asset: Annotated[str, Field(description='the avatar decoration hash')]
    sku_id: Annotated[
        SnowflakeType | None, Field(description="id of the avatar decoration's SKU")
    ]
