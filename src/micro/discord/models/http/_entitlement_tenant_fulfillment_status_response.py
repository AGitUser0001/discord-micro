# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class EntitlementTenantFulfillmentStatusResponse(IntEnum):
    UNKNOWN = 0
    FULFILLMENT_NOT_NEEDED = 1
    FULFILLMENT_NEEDED = 2
    FULFILLED = 3
    FULFILLMENT_FAILED = 4
    UNFULFILLMENT_NEEDED = 5
    UNFULFILLED = 6
    UNFULFILLMENT_FAILED = 7
