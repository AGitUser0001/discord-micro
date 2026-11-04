# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._nameplate_palette import NameplatePalette
from ._snowflake_type import SnowflakeType


class UserNameplateResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    sku_id: Annotated[
        SnowflakeType | None, Field(description='ID of the nameplate SKU')
    ]
    asset: Annotated[str, Field(description='Path to the nameplate asset')]
    label: Annotated[
        str, Field(description='The label of this nameplate. Currently unused')
    ]
    palette: Annotated[
        NameplatePalette, Field(description='Background color of the nameplate')
    ]
