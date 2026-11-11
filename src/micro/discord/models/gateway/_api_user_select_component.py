# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_select_menu_default_value_user import APISelectMenuDefaultValueUser


class APIUserSelectComponent(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: Annotated[Literal[5], Field(description='The type of the component')]
    id: Annotated[
        float | None,
        Field(
            description="32 bit integer used as an optional identifier for component\n\nThe id field is optional and is used to identify components in the response from an interaction that aren't interactive components. The id must be unique within the message and is generated sequentially if left empty. Generation of ids won't use another id that exists in the message if you have one defined for another component."
        ),
    ] = None
    custom_id: Annotated[
        str,
        Field(
            description='A developer-defined identifier for the select menu, max 100 characters'
        ),
    ]
    placeholder: Annotated[
        str | None,
        Field(
            description='Custom placeholder text if nothing is selected, max 150 characters'
        ),
    ] = None
    min_values: Annotated[
        float | None,
        Field(
            description='The minimum number of items that must be chosen; min 0, max 25'
        ),
    ] = None
    max_values: Annotated[
        float | None,
        Field(description='The maximum number of items that can be chosen; max 25'),
    ] = None
    disabled: Annotated[bool | None, Field(description='Disable the select')] = None
    required: Annotated[
        bool | None,
        Field(description='Whether the component is required to answer in a modal.'),
    ] = None
    default_values: Annotated[
        list[APISelectMenuDefaultValueUser] | None,
        Field(
            description='List of default values for auto-populated select menu components'
        ),
    ] = None
