# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class NameplatePalette(StrEnum):
    CRIMSON = 'crimson'
    BERRY = 'berry'
    SKY = 'sky'
    TEAL = 'teal'
    FOREST = 'forest'
    BUBBLE_GUM = 'bubble_gum'
    VIOLET = 'violet'
    COBALT = 'cobalt'
    CLOVER = 'clover'
    LEMON = 'lemon'
    WHITE = 'white'
    BLACK = 'black'
