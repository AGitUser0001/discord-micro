# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._interaction_types import InteractionTypes
from ._snowflake_type import SnowflakeType
from ._user_response import UserResponse


class MessageComponentInteractionMetadataResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    type: InteractionTypes
    user: UserResponse | None = None
    authorizing_integration_owners: dict[str, SnowflakeType]
    original_response_message_id: SnowflakeType | None = None
    interacted_message_id: SnowflakeType
