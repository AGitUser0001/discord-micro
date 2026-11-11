# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class APIButtonComponentWithSKUId(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Literal[2], Field(description='The type of the component')]
    id: Annotated[
        float | None,
        Field(
            description="32 bit integer used as an optional identifier for component\n\nThe id field is optional and is used to identify components in the response from an interaction that aren't interactive components. The id must be unique within the message and is generated sequentially if left empty. Generation of ids won't use another id that exists in the message if you have one defined for another component."
        ),
    ] = None
    style: Annotated[Literal[6], Field(description='The style of the button')]
    disabled: Annotated[bool | None, Field(description='The status of the button')] = (
        None
    )
    sku_id: Annotated[str, Field(description='The id for a purchasable SKU')]
