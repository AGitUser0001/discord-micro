# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class AfkTimeout(IntEnum):
    integer_60 = 60
    integer_300 = 300
    integer_900 = 900
    integer_1800 = 1800
    integer_3600 = 3600
