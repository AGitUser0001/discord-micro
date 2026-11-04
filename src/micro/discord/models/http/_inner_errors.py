# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._error import Error


class InnerErrors(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    field_errors: Annotated[
        list[Error],
        Field(alias='_errors', description='The list of errors for this field'),
    ]
