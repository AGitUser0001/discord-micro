# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._error import Error
from ._error_details import ErrorDetails


class ErrorResponse(Error):
    model_config = ConfigDict(
        extra='allow',
    )
    errors: ErrorDetails | None = None
