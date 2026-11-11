# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_interaction_data_resolved_guild_member import APIInteractionDataResolvedGuildMember


class RecordstringAPIInteractionDataResolvedGuildMember(
    RootModel[dict[str, APIInteractionDataResolvedGuildMember]]
):
    root: dict[str, APIInteractionDataResolvedGuildMember]
