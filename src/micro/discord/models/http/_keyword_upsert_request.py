# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._automod_event_type import AutomodEventType
from ._automod_trigger_type import AutomodTriggerType
from ._keyword_trigger_metadata import KeywordTriggerMetadata
from ._snowflake_type import SnowflakeType
from ._block_message_action import BlockMessageAction
from ._quarantine_user_action import QuarantineUserAction
from ._user_communication_disabled_action import UserCommunicationDisabledAction
from ._flag_to_channel_action import FlagToChannelAction


class KeywordUpsertRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(max_length=100)]
    event_type: AutomodEventType
    actions: Annotated[
        list[
            BlockMessageAction
            | FlagToChannelAction
            | QuarantineUserAction
            | UserCommunicationDisabledAction
        ]
        | None,
        Field(max_length=5, min_length=1),
    ] = None
    enabled: bool | None = None
    exempt_roles: Annotated[list[SnowflakeType] | None, Field(max_length=20)] = None
    exempt_channels: Annotated[list[SnowflakeType] | None, Field(max_length=50)] = None
    trigger_type: AutomodTriggerType
    trigger_metadata: KeywordTriggerMetadata | None = None
