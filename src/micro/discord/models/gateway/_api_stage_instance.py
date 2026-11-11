# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._privacy_level import PrivacyLevel


class APIStageInstance(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the stage instance')]
    guild_id: Annotated[
        str, Field(description='The guild id of the associated stage channel')
    ]
    channel_id: Annotated[
        str, Field(description='The id of the associated stage channel')
    ]
    topic: Annotated[
        str, Field(description='The topic of the stage instance (1-120 characters)')
    ]
    privacy_level: Annotated[
        PrivacyLevel, Field(description='The privacy level of the stage instance')
    ]
    discoverable_disabled: Annotated[
        bool,
        Field(
            deprecated=True, description='Whether or not stage discovery is disabled'
        ),
    ]
    guild_scheduled_event_id: Annotated[
        str | None,
        Field(description='The id of the scheduled event for this stage instance'),
    ] = None
