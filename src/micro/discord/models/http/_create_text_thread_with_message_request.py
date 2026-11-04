# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._thread_auto_archive_duration import ThreadAutoArchiveDuration


class CreateTextThreadWithMessageRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(max_length=100, min_length=1)]
    auto_archive_duration: ThreadAutoArchiveDuration | None = None
    rate_limit_per_user: Annotated[int | None, Field(ge=0, le=21600)] = None
