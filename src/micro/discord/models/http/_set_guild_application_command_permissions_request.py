# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_permission import ApplicationCommandPermission


class SetGuildApplicationCommandPermissionsRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    permissions: Annotated[
        list[ApplicationCommandPermission] | None, Field(max_length=100)
    ] = None
