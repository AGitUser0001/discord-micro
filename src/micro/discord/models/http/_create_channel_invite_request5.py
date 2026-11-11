# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._create_channel_invite_request3 import CreateChannelInviteRequest3
from ._create_guild_invite_request import CreateGuildInviteRequest


class CreateChannelInviteRequest5(
    CreateGuildInviteRequest, CreateChannelInviteRequest3
):
    model_config = ConfigDict(
        extra='allow',
    )
