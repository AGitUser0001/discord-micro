# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._automod_event_type import AutomodEventType
from ._automod_trigger_type import AutomodTriggerType
from ._block_message_action_response import BlockMessageActionResponse
from ._default_keyword_list_trigger_metadata_response import DefaultKeywordListTriggerMetadataResponse
from ._quarantine_user_action_response import QuarantineUserActionResponse
from ._snowflake_type import SnowflakeType
from ._user_communication_disabled_action_response import UserCommunicationDisabledActionResponse
from ._flag_to_channel_action_response import FlagToChannelActionResponse


class DefaultKeywordRuleResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    guild_id: SnowflakeType
    creator_id: SnowflakeType
    name: str
    event_type: AutomodEventType
    actions: list[
        BlockMessageActionResponse
        | FlagToChannelActionResponse
        | QuarantineUserActionResponse
        | UserCommunicationDisabledActionResponse
    ]
    trigger_type: AutomodTriggerType
    enabled: bool
    exempt_roles: list[SnowflakeType]
    exempt_channels: list[SnowflakeType]
    trigger_metadata: DefaultKeywordListTriggerMetadataResponse
