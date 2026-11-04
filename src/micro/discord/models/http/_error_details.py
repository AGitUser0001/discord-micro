# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._inner_errors import InnerErrors


class ErrorDetails(RootModel[Union[dict[str, "ErrorDetails"], InnerErrors]]):
    root: Union[dict[str, "ErrorDetails"], InnerErrors]


ErrorDetails.model_rebuild()
