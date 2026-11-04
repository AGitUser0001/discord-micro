# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._new_member_action_type import NewMemberActionType
from ._snowflake_type import SnowflakeType
from ._settings_emoji_response import SettingsEmojiResponse


class NewMemberActionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    channel_id: SnowflakeType
    action_type: NewMemberActionType
    title: str
    description: str
    emoji: SettingsEmojiResponse | None = None
    icon: str | None = None
