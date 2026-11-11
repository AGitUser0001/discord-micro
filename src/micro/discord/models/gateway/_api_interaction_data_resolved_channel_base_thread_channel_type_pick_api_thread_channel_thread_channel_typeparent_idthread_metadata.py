# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_thread_metadata import APIThreadMetadata
from ._thread_channel_type import ThreadChannelType


class APIInteractionDataResolvedChannelBaseThreadChannelTypePickAPIThreadChannelThreadChannelTypeparentIdthreadMetadata(
    BaseModel
):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    name: Annotated[
        str | None, Field(description='The name of the channel (1-100 characters)')
    ]
    thread_metadata: Annotated[
        APIThreadMetadata | None,
        Field(
            description='The metadata for a thread channel not shared by other channels'
        ),
    ] = None
    parent_id: Annotated[
        str | None, Field(description='ID of the parent channel for the thread')
    ] = None
    type: ThreadChannelType
    permissions: str
    app_permissions: str | None = None
