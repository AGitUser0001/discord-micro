# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._create_group_dm_invite_request import CreateGroupDMInviteRequest
from ._create_channel_invite_request3 import CreateChannelInviteRequest3


class CreateChannelInviteRequest4(
    CreateGroupDMInviteRequest, CreateChannelInviteRequest3
):
    model_config = ConfigDict(
        extra='allow',
    )
