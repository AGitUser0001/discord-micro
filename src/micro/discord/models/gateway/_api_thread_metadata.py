# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._auto_archive_duration import AutoArchiveDuration


class APIThreadMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    archived: Annotated[bool, Field(description='Whether the thread is archived')]
    auto_archive_duration: Annotated[
        AutoArchiveDuration,
        Field(
            description='Duration in minutes to automatically archive the thread after recent activity, can be set to: 60, 1440, 4320, 10080'
        ),
    ]
    archive_timestamp: Annotated[
        str,
        Field(
            description="An ISO8601 timestamp when the thread's archive status was last changed, used for calculating recent activity"
        ),
    ]
    locked: Annotated[
        bool,
        Field(
            description='Whether the thread is locked; when a thread is locked, only users with `MANAGE_THREADS` can unarchive it'
        ),
    ]
    invitable: Annotated[
        bool | None,
        Field(
            description='Whether non-moderators can add other non-moderators to the thread; only available on private threads'
        ),
    ] = None
    create_timestamp: Annotated[
        str | None,
        Field(
            description='Timestamp when the thread was created; only populated for threads created after 2022-01-09'
        ),
    ] = None
