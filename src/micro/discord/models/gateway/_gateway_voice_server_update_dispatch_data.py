# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayVoiceServerUpdateDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    token: Annotated[str, Field(description='Voice connection token')]
    guild_id: Annotated[
        str, Field(description='The guild this voice server update is for')
    ]
    endpoint: Annotated[
        str | None,
        Field(
            description='The voice server host\n\nA `null` endpoint means that the voice server allocated has gone away and is trying to be reallocated.\nYou should attempt to disconnect from the currently connected voice server, and not attempt to reconnect\nuntil a new voice server is allocated'
        ),
    ]
