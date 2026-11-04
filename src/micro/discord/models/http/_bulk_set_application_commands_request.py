# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_update_request import ApplicationCommandUpdateRequest


class BulkSetApplicationCommandsRequest(
    RootModel[list[ApplicationCommandUpdateRequest] | None]
):
    root: Annotated[list[ApplicationCommandUpdateRequest] | None, Field(max_length=130)]
