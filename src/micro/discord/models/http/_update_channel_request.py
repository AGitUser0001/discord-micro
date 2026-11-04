# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._update_dm_request_partial import UpdateDMRequestPartial
from ._update_group_dm_request_partial import UpdateGroupDMRequestPartial
from ._update_guild_channel_request_partial import UpdateGuildChannelRequestPartial
from ._update_thread_request_partial import UpdateThreadRequestPartial


class UpdateChannelRequest(
    RootModel[
        UpdateDMRequestPartial
        | UpdateGroupDMRequestPartial
        | UpdateGuildChannelRequestPartial
        | UpdateThreadRequestPartial
    ]
):
    root: (
        UpdateDMRequestPartial
        | UpdateGroupDMRequestPartial
        | UpdateGuildChannelRequestPartial
        | UpdateThreadRequestPartial
    )
