# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._int53_type import Int53Type


class ApplicationCommandOptionIntegerChoiceResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: str
    name_localized: str | None = None
    name_localizations: dict[str, Any] | None = None
    value: Int53Type
