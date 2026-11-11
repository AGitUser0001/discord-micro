# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_response import ApplicationCommandResponse


class BulkSetApplicationCommandsResponse200(
    RootModel[list[ApplicationCommandResponse] | None]
):
    root: list[ApplicationCommandResponse] | None
