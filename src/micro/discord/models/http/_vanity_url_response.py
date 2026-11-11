# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._vanity_url_error_response import VanityURLErrorResponse


class VanityURLResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    code: str | None
    uses: int
    error: VanityURLErrorResponse | None = None
