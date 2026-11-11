# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_button_component_with_url_type_o1 import APIButtonComponentWithURLTypeO1
from ._api_button_component_with_url_type import APIButtonComponentWithURLType


class APIComponentEmbedButton(
    RootModel[APIButtonComponentWithURLType | APIButtonComponentWithURLTypeO1]
):
    root: Annotated[
        APIButtonComponentWithURLType | APIButtonComponentWithURLTypeO1,
        Field(
            description='A button must use the link style (`style` of `5`) and may contain `id`, `type`, `url`, `style`, `label`, `emoji`,\nand `disabled`, with a `label`, an `emoji`, or both. Any other key invalidates the entire payload.'
        ),
    ]
