# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._create_group_dm_invite_request import CreateGroupDMInviteRequest
from ._create_guild_invite_request import CreateGuildInviteRequest


class CreateChannelInviteRequest(
    RootModel[CreateGroupDMInviteRequest | CreateGuildInviteRequest]
):
    root: CreateGroupDMInviteRequest | CreateGuildInviteRequest
