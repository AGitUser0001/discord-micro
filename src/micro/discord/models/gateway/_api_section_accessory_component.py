# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_button_component_with_sku_id import APIButtonComponentWithSKUId
from ._api_button_component_with_url import APIButtonComponentWithURL
from ._api_thumbnail_component import APIThumbnailComponent
from ._api_button_component_with_custom_id import APIButtonComponentWithCustomId


class APISectionAccessoryComponent(
    RootModel[
        APIButtonComponentWithCustomId
        | APIButtonComponentWithSKUId
        | APIButtonComponentWithURL
        | APIThumbnailComponent
    ]
):
    root: (
        APIButtonComponentWithCustomId
        | APIButtonComponentWithSKUId
        | APIButtonComponentWithURL
        | APIThumbnailComponent
    )
