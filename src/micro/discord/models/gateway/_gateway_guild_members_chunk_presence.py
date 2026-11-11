# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_presence_client_status import GatewayPresenceClientStatus
from ._status4 import Status4
from ._partial_api_user_pick_api_userid import PartialAPIUserPickAPIUserid
from ._gateway_activity import GatewayActivity


class GatewayGuildMembersChunkPresence(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    user: Annotated[
        PartialAPIUserPickAPIUserid,
        Field(
            description='The user presence is being updated for\n\n**The user object within this event can be partial, the only field which must be sent is the `id` field,\neverything else is optional.**'
        ),
    ]
    status: Annotated[
        Status4 | None,
        Field(description='Either "idle", "dnd", "online", or "offline"'),
    ] = None
    activities: Annotated[
        list[GatewayActivity] | None, Field(description="User's current activities")
    ] = None
    client_status: Annotated[
        GatewayPresenceClientStatus | None,
        Field(description="User's platform-dependent status"),
    ] = None
