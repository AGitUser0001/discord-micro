# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class Flags41(IntEnum):
    integer_1 = 1
    integer_2 = 2
    integer_4 = 4
    integer_16 = 16
    integer_32 = 32
    integer_128 = 128
    integer_256 = 256
    integer_512 = 512
    integer_32768 = 32768
    integer_2097152 = 2097152
