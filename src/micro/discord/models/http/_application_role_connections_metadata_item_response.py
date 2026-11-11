# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._metadata_item_types import MetadataItemTypes


class ApplicationRoleConnectionsMetadataItemResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MetadataItemTypes
    key: str
    name: str
    name_localizations: dict[str, Any] | None = None
    description: str
    description_localizations: dict[str, Any] | None = None
