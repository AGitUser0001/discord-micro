# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._palette import Palette


class APINameplateData(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sku_id: Annotated[str, Field(description='ID of the nameplate SKU')]
    asset: Annotated[str, Field(description='Path to the nameplate asset')]
    label: Annotated[
        str, Field(description='The label of this nameplate. Currently unused')
    ]
    palette: Annotated[Palette, Field(description='Background color of the nameplate')]
