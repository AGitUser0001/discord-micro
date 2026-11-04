# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._user_select_default_value_response import UserSelectDefaultValueResponse
from ._role_select_default_value_response import RoleSelectDefaultValueResponse


class MentionableSelectComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    custom_id: str
    placeholder: str | None = None
    min_values: int
    max_values: int
    disabled: bool | None = None
    default_values: (
        list[RoleSelectDefaultValueResponse | UserSelectDefaultValueResponse] | None
    ) = None
