# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class SearchIndexNotReadyResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    message: str
    code: int
    documents_indexed: int
    retry_after: int
