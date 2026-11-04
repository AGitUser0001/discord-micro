# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._user_select_component_for_message_request import UserSelectComponentForMessageRequest
from ._button_component_for_message_request import ButtonComponentForMessageRequest
from ._channel_select_component_for_message_request import ChannelSelectComponentForMessageRequest
from ._mentionable_select_component_for_message_request import MentionableSelectComponentForMessageRequest
from ._role_select_component_for_message_request import RoleSelectComponentForMessageRequest
from ._string_select_component_for_message_request import StringSelectComponentForMessageRequest


class ActionRowComponentForMessageRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    components: Annotated[
        list[
            ButtonComponentForMessageRequest
            | ChannelSelectComponentForMessageRequest
            | MentionableSelectComponentForMessageRequest
            | RoleSelectComponentForMessageRequest
            | StringSelectComponentForMessageRequest
            | UserSelectComponentForMessageRequest
        ],
        Field(max_length=5, min_length=1),
    ]
