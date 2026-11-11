# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_thread_member import APIThreadMember


class GatewayThreadMembersUpdate(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[
        str,
        Field(description='The id of the thread for which members are being synced'),
    ]
    guild_id: Annotated[
        str, Field(description='The id of the guild that the thread is in')
    ]
    member_count: Annotated[
        float,
        Field(
            description='The approximate member count of the thread, does not count above 50 even if there are more members'
        ),
    ]
    added_members: Annotated[
        list[APIThreadMember] | None,
        Field(description='The members that were added to the thread'),
    ] = None
    removed_member_ids: Annotated[
        list[str] | None,
        Field(description='The ids of the members that were removed from the thread'),
    ] = None
