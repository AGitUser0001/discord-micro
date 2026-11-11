# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_heartbeat import GatewayHeartbeat
from ._gateway_request_channel_info import GatewayRequestChannelInfo
from ._gateway_request_soundboard_sounds import GatewayRequestSoundboardSounds
from ._gateway_resume import GatewayResume
from ._gateway_update_presence import GatewayUpdatePresence
from ._gateway_voice_state_update import GatewayVoiceStateUpdate
from ._gateway_request_guild_members import GatewayRequestGuildMembers
from ._gateway_identify import GatewayIdentify


class GatewaySendPayload(
    RootModel[
        GatewayHeartbeat
        | GatewayIdentify
        | GatewayRequestChannelInfo
        | GatewayRequestGuildMembers
        | GatewayRequestSoundboardSounds
        | GatewayResume
        | GatewayUpdatePresence
        | GatewayVoiceStateUpdate
    ]
):
    root: Annotated[
        GatewayHeartbeat
        | GatewayIdentify
        | GatewayRequestChannelInfo
        | GatewayRequestGuildMembers
        | GatewayRequestSoundboardSounds
        | GatewayResume
        | GatewayUpdatePresence
        | GatewayVoiceStateUpdate,
        Field(discriminator='op'),
    ]
