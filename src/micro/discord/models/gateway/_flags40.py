# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class Flags40(IntFlag):
    integer_16 = 16
    integer_32 = 32
    integer_64 = 64
    integer_128 = 128
