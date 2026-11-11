# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._flags24 import Flags24
from ._api_user import APIUser


class PartialAPIDMChannelPickAPIChannelidtype(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    type: Annotated[Literal[1], Field(description='A direct message between users')]
    flags: Flags24 | None = None
    rate_limit_per_user: Annotated[
        float | None,
        Field(
            description='Amount of seconds a user has to wait before sending another message (0-21600);\nbots, as well as users with the permission `BYPASS_SLOWMODE`, are unaffected\n\n`rate_limit_per_user` also applies to thread creation. Users can send one message and create one thread during each `rate_limit_per_user` interval.\n\nFor thread channels, `rate_limit_per_user` is only returned if the field is set to a non-zero and non-null value.\nThe absence of this field in API calls and Gateway events should indicate that slowmode has been reset to the default value.'
        ),
    ] = None
    last_message_id: Annotated[
        str | None,
        Field(
            description='The id of the last message sent in this channel (may not point to an existing or valid message)'
        ),
    ] = None
    last_pin_timestamp: Annotated[
        str | None,
        Field(
            description='When the last pinned message was pinned.\nThis may be `null` in events such as `GUILD_CREATE` when a message is not pinned'
        ),
    ] = None
    recipients: Annotated[
        list[APIUser] | None, Field(description='The recipients of the DM')
    ] = None
    name: Annotated[
        None, Field(description='The name of the channel (always null for DM channels)')
    ] = None
