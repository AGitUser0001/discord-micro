# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_scheduled_event_user_responses import GuildScheduledEventUserResponses
from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse
from ._guild_member_response import GuildMemberResponse


class ScheduledEventUserResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    guild_scheduled_event_id: Annotated[
        SnowflakeType, Field(description='ID of the scheduled event')
    ]
    guild_scheduled_event_exception_id: Annotated[
        SnowflakeType | None, Field(description='ID of the scheduled event exception')
    ] = None
    user_id: Annotated[SnowflakeType, Field(description='ID of the user')]
    user: Annotated[
        UserResponse | None, Field(description='User object for the RSVP user')
    ] = None
    member: Annotated[
        GuildMemberResponse | None,
        Field(description='Guild member object for the RSVP user'),
    ] = None
    response: Annotated[
        GuildScheduledEventUserResponses,
        Field(description="User's RSVP status for the event"),
    ]
