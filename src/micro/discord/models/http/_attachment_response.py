# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse
from ._application_response import ApplicationResponse


class AttachmentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    filename: str
    size: int
    url: AnyUrl
    proxy_url: AnyUrl
    width: int | None = None
    height: int | None = None
    duration_secs: float | None = None
    waveform: str | None = None
    description: str | None = None
    content_type: str | None = None
    ephemeral: bool | None = None
    flags: int | None = None
    placeholder: str | None = None
    placeholder_version: int | None = None
    title: str | None = None
    application: ApplicationResponse | None = None
    clip_created_at: AwareDatetime | None = None
    clip_participants: list[UserResponse] | None = None
