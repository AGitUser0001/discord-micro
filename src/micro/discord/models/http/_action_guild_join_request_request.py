# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_join_request_application_status import GuildJoinRequestApplicationStatus


class ActionGuildJoinRequestRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    action: Annotated[
        GuildJoinRequestApplicationStatus | None,
        Field(description='Whether to approve or reject the join request'),
    ] = None
    rejection_reason: Annotated[
        str | None,
        Field(
            description='Reason for rejection. Only used when action is REJECTED',
            max_length=160,
        ),
    ] = None
