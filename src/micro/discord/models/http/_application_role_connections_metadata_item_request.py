# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._metadata_item_types import MetadataItemTypes


class ApplicationRoleConnectionsMetadataItemRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MetadataItemTypes
    key: Annotated[str, Field(max_length=50, min_length=1)]
    name: Annotated[str, Field(max_length=100, min_length=1)]
    name_localizations: dict[str, Any] | None = None
    description: Annotated[str, Field(max_length=200, min_length=1)]
    description_localizations: dict[str, Any] | None = None
