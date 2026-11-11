# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_channel_response import GuildChannelResponse
from ._private_channel_response import PrivateChannelResponse
from ._private_group_channel_response import PrivateGroupChannelResponse
from ._thread_response import ThreadResponse


class GetChannelResponse200(
    RootModel[
        GuildChannelResponse
        | PrivateChannelResponse
        | PrivateGroupChannelResponse
        | ThreadResponse
    ]
):
    root: (
        GuildChannelResponse
        | PrivateChannelResponse
        | PrivateGroupChannelResponse
        | ThreadResponse
    )
