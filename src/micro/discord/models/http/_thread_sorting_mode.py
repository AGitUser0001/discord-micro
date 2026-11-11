# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class ThreadSortingMode(StrEnum):
    RELEVANCE = 'relevance'
    CREATION_TIME = 'creation_time'
    LAST_MESSAGE_TIME = 'last_message_time'
    ARCHIVE_TIME = 'archive_time'
