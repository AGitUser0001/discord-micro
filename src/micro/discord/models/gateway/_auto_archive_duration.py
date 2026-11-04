# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class AutoArchiveDuration(IntEnum):
    integer_60 = 60
    integer_1440 = 1440
    integer_4320 = 4320
    integer_10080 = 10080
