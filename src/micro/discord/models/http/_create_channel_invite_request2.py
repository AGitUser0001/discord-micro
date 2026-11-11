# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._create_channel_invite_request4 import CreateChannelInviteRequest4
from ._create_channel_invite_request5 import CreateChannelInviteRequest5


class CreateChannelInviteRequest2(
    RootModel[CreateChannelInviteRequest4 | CreateChannelInviteRequest5]
):
    root: CreateChannelInviteRequest4 | CreateChannelInviteRequest5
