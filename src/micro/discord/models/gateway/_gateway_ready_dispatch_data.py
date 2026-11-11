# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_unavailable_guild import APIUnavailableGuild
from ._pick_api_applicationflagsflags_newid import PickAPIApplicationflagsflagsNewid
from ._api_user import APIUser


class GatewayReadyDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    v: Annotated[float, Field(description='Gateway version')]
    user: Annotated[
        APIUser, Field(description='Information about the user including email')
    ]
    guilds: Annotated[
        list[APIUnavailableGuild], Field(description='The guilds the user is in')
    ]
    session_id: Annotated[str, Field(description='Used for resuming connections')]
    resume_gateway_url: Annotated[
        str, Field(description='Gateway url for resuming connections')
    ]
    shard: Annotated[
        list[float] | None,
        Field(
            description='The shard information associated with this session, if sent when identifying',
            max_length=2,
            min_length=2,
        ),
    ] = None
    application: Annotated[
        PickAPIApplicationflagsflagsNewid,
        Field(description='Contains `id`, `flags`, and `flags_new`'),
    ]
