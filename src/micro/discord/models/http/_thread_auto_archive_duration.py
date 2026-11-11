# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ThreadAutoArchiveDuration(IntEnum):
    ONE_HOUR = 60
    ONE_DAY = 1440
    THREE_DAY = 4320
    SEVEN_DAY = 10080
