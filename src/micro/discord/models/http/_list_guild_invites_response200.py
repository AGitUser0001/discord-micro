# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._friend_invite_response import FriendInviteResponse
from ._group_dm_invite_response import GroupDMInviteResponse
from ._guild_invite_response import GuildInviteResponse


class ListGuildInvitesResponse200(
    RootModel[
        list[FriendInviteResponse | GroupDMInviteResponse | GuildInviteResponse | None]
        | None
    ]
):
    root: (
        list[FriendInviteResponse | GroupDMInviteResponse | GuildInviteResponse | None]
        | None
    )
