# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class SKUIneligibilityReason(IntEnum):
    OTHER = 0
    OWNS_SKU_OR_BUNDLE_COMPONENT = 1
    PLATFORM_RESTRICTION = 2
