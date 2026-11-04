# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._sku_ids import SkuIds


class GetCurrentUserApplicationEntitlementsParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sku_ids: str | SkuIds | None = None
    exclude_consumed: bool | None = None
