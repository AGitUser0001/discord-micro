# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_external_guild_scheduled_event import APIExternalGuildScheduledEvent
from ._api_stage_instance_guild_scheduled_event import APIStageInstanceGuildScheduledEvent
from ._api_voice_guild_scheduled_event import APIVoiceGuildScheduledEvent


class APIGuildScheduledEvent(
    RootModel[
        APIExternalGuildScheduledEvent
        | APIStageInstanceGuildScheduledEvent
        | APIVoiceGuildScheduledEvent
    ]
):
    root: Annotated[
        APIExternalGuildScheduledEvent
        | APIStageInstanceGuildScheduledEvent
        | APIVoiceGuildScheduledEvent,
        Field(discriminator='entity_type'),
    ]
