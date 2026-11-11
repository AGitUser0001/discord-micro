# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_role_connections_metadata_item_request import ApplicationRoleConnectionsMetadataItemRequest


class UpdateApplicationRoleConnectionsMetadataRequest(
    RootModel[list[ApplicationRoleConnectionsMetadataItemRequest] | None]
):
    root: Annotated[
        list[ApplicationRoleConnectionsMetadataItemRequest] | None, Field(max_length=5)
    ]
