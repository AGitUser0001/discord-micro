# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class AutomodActionType(IntEnum):
    BLOCK_MESSAGE = 1
    FLAG_TO_CHANNEL = 2
    USER_COMMUNICATION_DISABLED = 3
    QUARANTINE_USER = 4
