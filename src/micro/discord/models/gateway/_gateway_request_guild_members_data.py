# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_request_guild_members_data_with_query import GatewayRequestGuildMembersDataWithQuery
from ._gateway_request_guild_members_data_with_user_ids import GatewayRequestGuildMembersDataWithUserIds


class GatewayRequestGuildMembersData(
    RootModel[
        GatewayRequestGuildMembersDataWithQuery
        | GatewayRequestGuildMembersDataWithUserIds
    ]
):
    root: (
        GatewayRequestGuildMembersDataWithQuery
        | GatewayRequestGuildMembersDataWithUserIds
    )
