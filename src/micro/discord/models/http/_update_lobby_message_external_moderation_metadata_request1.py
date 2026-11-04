# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._update_lobby_message_external_moderation_metadata_request_additional_property import UpdateLobbyMessageExternalModerationMetadataRequestAdditionalProperty


class UpdateLobbyMessageExternalModerationMetadataRequest1(
    RootModel[
        dict[str, UpdateLobbyMessageExternalModerationMetadataRequestAdditionalProperty]
    ]
):
    root: Annotated[
        dict[
            str, UpdateLobbyMessageExternalModerationMetadataRequestAdditionalProperty
        ],
        Field(max_length=5),
    ]
