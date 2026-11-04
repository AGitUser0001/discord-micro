# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._private_channel_response import PrivateChannelResponse
from ._private_group_channel_response import PrivateGroupChannelResponse


class AddGroupDmUserResponse201(
    RootModel[PrivateChannelResponse | PrivateGroupChannelResponse]
):
    root: PrivateChannelResponse | PrivateGroupChannelResponse
