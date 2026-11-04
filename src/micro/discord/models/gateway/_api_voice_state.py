# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_guild_member import APIGuildMember


class APIVoiceState(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: Annotated[
        str | None, Field(description='The channel id this user is connected to')
    ]
    user_id: Annotated[str, Field(description='The user id this voice state is for')]
    member: Annotated[
        APIGuildMember | None,
        Field(description='The guild member this voice state is for'),
    ] = None
    session_id: Annotated[str, Field(description='The session id for this voice state')]
    deaf: Annotated[
        bool, Field(description='Whether this user is deafened by the server')
    ]
    mute: Annotated[bool, Field(description='Whether this user is muted by the server')]
    self_deaf: Annotated[
        bool, Field(description='Whether this user is locally deafened')
    ]
    self_mute: Annotated[bool, Field(description='Whether this user is locally muted')]
    self_stream: Annotated[
        bool | None, Field(description='Whether this user is streaming using "Go Live"')
    ] = None
    self_video: Annotated[
        bool, Field(description="Whether this user's camera is enabled")
    ]
    suppress: Annotated[
        bool, Field(description='Whether this user is muted by the current user')
    ]
    request_to_speak_timestamp: Annotated[
        str | None, Field(description='The time at which the user requested to speak')
    ]
    guild_id: Annotated[
        str | None, Field(description='The guild id this voice state is for')
    ] = None
