# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class IntegrationExpireGracePeriodTypes(IntEnum):
    ONE_DAY = 1
    THREE_DAYS = 3
    SEVEN_DAYS = 7
    FOURTEEN_DAYS = 14
    THIRTY_DAYS = 30
