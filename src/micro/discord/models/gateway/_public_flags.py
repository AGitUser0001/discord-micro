# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class PublicFlags(IntFlag):
    integer_1 = 1
    integer_2 = 2
    integer_4 = 4
    integer_8 = 8
    integer_16 = 16
    integer_32 = 32
    integer_64 = 64
    integer_128 = 128
    integer_256 = 256
    integer_512 = 512
    integer_1024 = 1024
    integer_8192 = 8192
    integer_16384 = 16384
    integer_65536 = 65536
    integer_131072 = 131072
    integer_262144 = 262144
    integer_524288 = 524288
    integer_1048576 = 1048576
    integer_2097152 = 2097152
    integer_4194304 = 4194304
    integer_17592186044416 = 17592186044416
    integer_1125899906842624 = 1125899906842624
    integer_2251799813685248 = 2251799813685248
