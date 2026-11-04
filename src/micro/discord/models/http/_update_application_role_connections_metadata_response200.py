# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_role_connections_metadata_item_response import ApplicationRoleConnectionsMetadataItemResponse


class UpdateApplicationRoleConnectionsMetadataResponse200(
    RootModel[list[ApplicationRoleConnectionsMetadataItemResponse] | None]
):
    root: list[ApplicationRoleConnectionsMetadataItemResponse] | None
