# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._loading_state import LoadingState
from ._unfurled_media_item_content_scan_metadata import UnfurledMediaItemContentScanMetadata


class APIUnfurledMediaItem(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    url: Annotated[
        str,
        Field(
            description='Supports arbitrary urls and `attachment://<filename>` references'
        ),
    ]
    proxy_url: Annotated[
        str | None, Field(description='The proxied url of the media item')
    ] = None
    width: Annotated[
        float | None,
        Field(description='The width of the media item (if image or video)'),
    ] = None
    height: Annotated[
        float | None,
        Field(description='The height of the media item (if image or video)'),
    ] = None
    placeholder: Annotated[
        str | None, Field(description='ThumbHash placeholder (if image or video)')
    ] = None
    placeholder_version: Annotated[
        float | None,
        Field(description='Version of the placeholder (if image or video)'),
    ] = None
    content_type: Annotated[
        str | None, Field(description='The media type of the content')
    ] = None
    loading_state: LoadingState | None = None
    flags: Annotated[
        Literal[1] | None,
        Field(description='Unfurled media item flags combined as a bitfield'),
    ] = None
    content_scan_metadata: Annotated[
        UnfurledMediaItemContentScanMetadata | None,
        Field(description='Content scan metadata object'),
    ] = None
    attachment_id: Annotated[
        str | None, Field(description='The id of the uploaded attachment.')
    ] = None
