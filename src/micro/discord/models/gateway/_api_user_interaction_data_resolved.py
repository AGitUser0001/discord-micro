# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._recordstring_api_user import RecordstringAPIUser
from ._recordstring_api_interaction_data_resolved_guild_member import RecordstringAPIInteractionDataResolvedGuildMember


class APIUserInteractionDataResolved(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    users: RecordstringAPIUser
    members: RecordstringAPIInteractionDataResolvedGuildMember | None = None
