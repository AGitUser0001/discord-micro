# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class SnowflakeType(RootModel[str]):
    root: Annotated[str, Field(pattern='^(0|[1-9][0-9]*)$')]
