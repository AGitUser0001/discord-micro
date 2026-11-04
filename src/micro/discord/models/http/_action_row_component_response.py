# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._text_input_component_response import TextInputComponentResponse
from ._user_select_component_response import UserSelectComponentResponse
from ._button_component_response import ButtonComponentResponse
from ._channel_select_component_response import ChannelSelectComponentResponse
from ._mentionable_select_component_response import MentionableSelectComponentResponse
from ._role_select_component_response import RoleSelectComponentResponse
from ._string_select_component_response import StringSelectComponentResponse


class ActionRowComponentResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: int
    components: list[
        ButtonComponentResponse
        | ChannelSelectComponentResponse
        | MentionableSelectComponentResponse
        | RoleSelectComponentResponse
        | StringSelectComponentResponse
        | TextInputComponentResponse
        | UserSelectComponentResponse
    ]
