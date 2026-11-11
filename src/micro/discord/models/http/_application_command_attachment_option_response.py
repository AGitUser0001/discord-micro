# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._file_type1 import FileType1
from ._application_command_option_type import ApplicationCommandOptionType


class ApplicationCommandAttachmentOptionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: ApplicationCommandOptionType
    name: str
    name_localized: str | None = None
    name_localizations: dict[str, Any] | None = None
    description: str
    description_localized: str | None = None
    description_localizations: dict[str, Any] | None = None
    required: bool | None = None
    file_types: list[FileType1] | None = None
