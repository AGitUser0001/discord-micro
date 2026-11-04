# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_voice_channel_effect_send_dispatch_data import GatewayVoiceChannelEffectSendDispatchData


class GatewayVoiceChannelEffectSendDispatch(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    s: Annotated[
        float,
        Field(description='Sequence number, used for resuming sessions and heartbeats'),
    ]
    op: Annotated[Literal[0], Field(description='An event was dispatched')]
    t: Literal['VOICE_CHANNEL_EFFECT_SEND']
    d: GatewayVoiceChannelEffectSendDispatchData
