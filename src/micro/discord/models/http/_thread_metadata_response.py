# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._thread_auto_archive_duration import ThreadAutoArchiveDuration


class ThreadMetadataResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    archived: bool
    archive_timestamp: AwareDatetime | None
    auto_archive_duration: ThreadAutoArchiveDuration
    locked: bool
    create_timestamp: AwareDatetime | None = None
    invitable: bool | None = None
