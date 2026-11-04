# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_thread_member import APIThreadMember
from ._api_thread_channel_thread_channel_type import APIThreadChannelThreadChannelType


class GatewayThreadListSync(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_id: Annotated[str, Field(description='ID of the guild')]
    channel_ids: Annotated[
        list[str] | None,
        Field(
            description='The ids of all the parent channels whose threads are being synced, otherwise the entire guild'
        ),
    ] = None
    threads: Annotated[
        list[APIThreadChannelThreadChannelType],
        Field(description='Array of the synced threads'),
    ]
    members: Annotated[
        list[APIThreadMember],
        Field(
            description='The member objects for the client user in each joined thread that was synced'
        ),
    ]
