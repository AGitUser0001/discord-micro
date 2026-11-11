# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_private_thread_channel_type import APIPrivateThreadChannelType
from ._api_announcement_thread_channel_type import APIAnnouncementThreadChannelType
from ._api_public_thread_channel_type import APIPublicThreadChannelType


class Threads(
    RootModel[
        APIPublicThreadChannelType
        | APIPrivateThreadChannelType
        | APIAnnouncementThreadChannelType
    ]
):
    root: Annotated[
        APIPublicThreadChannelType
        | APIPrivateThreadChannelType
        | APIAnnouncementThreadChannelType,
        Field(discriminator='type'),
    ]
