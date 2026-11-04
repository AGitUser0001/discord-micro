# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_interaction_data_resolved_channel import APIInteractionDataResolvedChannel


class RecordstringAPIInteractionDataResolvedChannel(
    RootModel[dict[str, APIInteractionDataResolvedChannel]]
):
    root: dict[str, APIInteractionDataResolvedChannel]
