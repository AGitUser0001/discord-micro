# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._snowflake_type import SnowflakeType
from ._widget_activity import WidgetActivity
from ._widget_user_discriminator import WidgetUserDiscriminator


class WidgetMember(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: str
    username: str
    discriminator: WidgetUserDiscriminator
    avatar: None
    status: str
    avatar_url: AnyUrl
    activity: WidgetActivity | None = None
    deaf: bool | None = None
    mute: bool | None = None
    self_deaf: bool | None = None
    self_mute: bool | None = None
    suppress: bool | None = None
    channel_id: SnowflakeType | None = None
