# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class Flags60(IntFlag):
    integer_1 = 1
    integer_2 = 2
    integer_4 = 4
    integer_8 = 8
    integer_16 = 16
    integer_32 = 32
    integer_64 = 64
    integer_128 = 128
    integer_256 = 256
    integer_1024 = 1024
    integer_4096 = 4096
    integer_8192 = 8192
    integer_16384 = 16384
    integer_32768 = 32768
