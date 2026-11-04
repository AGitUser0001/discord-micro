# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._invite_types import InviteTypes
from ._invite_channel_response import InviteChannelResponse
from ._user_response import UserResponse


class GroupDMInviteResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: InviteTypes
    code: str
    inviter: UserResponse | None = None
    max_age: int | None = None
    created_at: AwareDatetime | None = None
    expires_at: AwareDatetime | None
    channel: InviteChannelResponse
    approximate_member_count: int | None = None
