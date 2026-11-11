# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._content_scan_metadata_response import ContentScanMetadataResponse
from ._snowflake_type import SnowflakeType


class UnfurledMediaResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    url: str
    proxy_url: str | None = None
    width: int | None = None
    height: int | None = None
    placeholder: str | None = None
    placeholder_version: int | None = None
    content_scan_metadata: ContentScanMetadataResponse | None = None
    content_type: str | None = None
    flags: int | None = None
    attachment_id: SnowflakeType | None = None
