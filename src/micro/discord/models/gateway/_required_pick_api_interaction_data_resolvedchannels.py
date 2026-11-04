# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._recordstring_api_interaction_data_resolved_channel import RecordstringAPIInteractionDataResolvedChannel


class RequiredPickAPIInteractionDataResolvedchannels(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channels: RecordstringAPIInteractionDataResolvedChannel
