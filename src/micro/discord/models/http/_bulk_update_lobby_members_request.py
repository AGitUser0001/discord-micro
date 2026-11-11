# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._bulk_lobby_member_request import BulkLobbyMemberRequest


class BulkUpdateLobbyMembersRequest(RootModel[list[BulkLobbyMemberRequest] | None]):
    root: Annotated[
        list[BulkLobbyMemberRequest] | None, Field(max_length=25, min_length=1)
    ]
