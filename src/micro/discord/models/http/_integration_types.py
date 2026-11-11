# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class IntegrationTypes(StrEnum):
    DISCORD = 'discord'
    TWITCH = 'twitch'
    YOUTUBE = 'youtube'
    GUILD_SUBSCRIPTION = 'guild_subscription'
