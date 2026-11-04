# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type14 import Type14


class APIInteractionDataResolvedChannelBaseGuildTextDMGuildVoiceGroupDMGuildCategoryGuildAnnouncementGuildStageVoiceGuildDirectoryGuildForumGuildMedia(
    BaseModel
):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='The id of the channel')]
    name: Annotated[
        str | None, Field(description='The name of the channel (1-100 characters)')
    ]
    type: Type14
    permissions: str
    app_permissions: str | None = None
