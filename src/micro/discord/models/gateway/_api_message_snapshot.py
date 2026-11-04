# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_message_snapshot_fields import APIMessageSnapshotFields


class APIMessageSnapshot(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    message: Annotated[
        APIMessageSnapshotFields,
        Field(description='Subset of the message object fields'),
    ]
    guild_id: Annotated[
        str | None,
        Field(deprecated=True, description="Id of the origin message's guild"),
    ] = None
