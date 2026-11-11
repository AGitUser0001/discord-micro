# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._purchase_type import PurchaseType
from ._guild_product_purchase_response import GuildProductPurchaseResponse


class PurchaseNotificationResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: PurchaseType
    guild_product_purchase: GuildProductPurchaseResponse | None = None
