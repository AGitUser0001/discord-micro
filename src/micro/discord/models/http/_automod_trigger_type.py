# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class AutomodTriggerType(IntEnum):
    KEYWORD = 1
    ML_SPAM = 3
    DEFAULT_KEYWORD_LIST = 4
    MENTION_SPAM = 5
    USER_PROFILE = 6
