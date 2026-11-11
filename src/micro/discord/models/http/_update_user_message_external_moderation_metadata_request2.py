# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._update_user_message_external_moderation_metadata_request_additional_property import UpdateUserMessageExternalModerationMetadataRequestAdditionalProperty


class UpdateUserMessageExternalModerationMetadataRequest2(
    RootModel[
        dict[str, UpdateUserMessageExternalModerationMetadataRequestAdditionalProperty]
    ]
):
    root: Annotated[
        dict[str, UpdateUserMessageExternalModerationMetadataRequestAdditionalProperty],
        Field(max_length=5),
    ]
