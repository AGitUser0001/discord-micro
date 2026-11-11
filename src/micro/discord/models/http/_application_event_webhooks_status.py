# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ApplicationEventWebhooksStatus(IntEnum):
    DISABLED = 1
    ENABLED = 2
    DISABLED_BY_DISCORD = 3
