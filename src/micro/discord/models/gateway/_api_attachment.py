# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags38 import Flags38
from ._api_user import APIUser
from ._api_application import APIApplication


class APIAttachment(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Attachment id')]
    filename: Annotated[str, Field(description='Name of file attached')]
    title: Annotated[
        str | None,
        Field(
            description='The original filename of the upload with special characters preserved\n\nThis will be present when the filename contains special characters (e.g. Cyrillic),\nin which case the `filename` field will be a sanitized version without those characters'
        ),
    ] = None
    description: Annotated[
        str | None,
        Field(description='Description (alt text) for the file (max 1024 characters)'),
    ] = None
    content_type: Annotated[
        str | None, Field(description="The attachment's media type")
    ] = None
    size: Annotated[float, Field(description='Size of file in bytes')]
    url: Annotated[str, Field(description='Source url of file')]
    proxy_url: Annotated[str, Field(description='A proxied url of file')]
    height: Annotated[
        float | None, Field(description='Height of file (if image or video)')
    ] = None
    width: Annotated[
        float | None, Field(description='Width of file (if image or video)')
    ] = None
    placeholder: Annotated[
        str | None, Field(description='ThumbHash placeholder (if image or video)')
    ] = None
    placeholder_version: Annotated[
        float | None,
        Field(description='Version of the placeholder (if image or video)'),
    ] = None
    ephemeral: Annotated[
        bool | None, Field(description='Whether this attachment is ephemeral')
    ] = None
    duration_secs: Annotated[
        float | None, Field(description='The duration of the audio or video file')
    ] = None
    waveform: Annotated[
        str | None,
        Field(
            description='Base64 encoded bytearray representing a sampled waveform (currently for voice messages)'
        ),
    ] = None
    flags: Annotated[
        Flags38 | None, Field(description='Attachment flags combined as a bitfield')
    ] = None
    clip_participants: Annotated[
        list[APIUser] | None,
        Field(description='For Clips, array of users who were in the stream'),
    ] = None
    clip_created_at: Annotated[
        str | None, Field(description='For Clips, when the clip was created')
    ] = None
    application: Annotated[
        APIApplication | None,
        Field(
            description='For Clips, the application in the stream, if recognized',
            discriminator='summary',
        ),
    ] = None
