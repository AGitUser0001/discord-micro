# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIIncidentsData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    invites_disabled_until: Annotated[
        str | None, Field(description='When invites get enabled again')
    ]
    dms_disabled_until: Annotated[
        str | None, Field(description='When direct messages get enabled again')
    ]
    dm_spam_detected_at: Annotated[
        str | None, Field(description='When the dm spam was detected')
    ] = None
    raid_detected_at: Annotated[
        str | None, Field(description='When the raid was detected')
    ] = None
