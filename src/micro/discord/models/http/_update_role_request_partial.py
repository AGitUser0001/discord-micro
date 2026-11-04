# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._role_colors import RoleColors


class UpdateRoleRequestPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str | None, Field(max_length=100, min_length=1)] = None
    permissions: int | None = None
    color: Annotated[int | None, Field(ge=0, le=16777215)] = None
    colors: RoleColors | None = None
    hoist: bool | None = None
    mentionable: bool | None = None
    icon: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    unicode_emoji: Annotated[str | None, Field(max_length=100)] = None
