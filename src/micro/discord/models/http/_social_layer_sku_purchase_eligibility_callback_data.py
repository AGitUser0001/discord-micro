# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._sku_ineligibility_reason import SKUIneligibilityReason


class SocialLayerSKUPurchaseEligibilityCallbackData(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    eligible: bool
    ineligible_reason: SKUIneligibilityReason | None = None
    ineligible_reason_description: Annotated[str | None, Field(max_length=255)] = None
