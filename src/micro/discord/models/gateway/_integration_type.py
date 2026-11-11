# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class IntegrationType(StrEnum):
    discord = 'discord'
    guild_subscription = 'guild_subscription'
    twitch = 'twitch'
    youtube = 'youtube'
