# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class GatewayIntegrationDeleteDispatchData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Integration id')]
    guild_id: Annotated[str, Field(description='ID of the guild')]
    application_id: Annotated[
        str | None,
        Field(
            description='ID of the bot/OAuth2 application for this Discord integration'
        ),
    ] = None
