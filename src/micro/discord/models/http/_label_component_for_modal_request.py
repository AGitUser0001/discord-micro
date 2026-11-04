# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._message_component_types import MessageComponentTypes
from ._checkbox_component_for_modal_request import CheckboxComponentForModalRequest
from ._checkbox_group_component_for_modal_request import CheckboxGroupComponentForModalRequest
from ._file_upload_component_for_modal_request import FileUploadComponentForModalRequest
from ._radio_group_component_for_modal_request import RadioGroupComponentForModalRequest
from ._text_input_component_for_modal_request import TextInputComponentForModalRequest
from ._user_select_component_for_modal_request import UserSelectComponentForModalRequest
from ._channel_select_component_for_modal_request import ChannelSelectComponentForModalRequest
from ._mentionable_select_component_for_modal_request import MentionableSelectComponentForModalRequest
from ._role_select_component_for_modal_request import RoleSelectComponentForModalRequest
from ._string_select_component_for_modal_request import StringSelectComponentForModalRequest


class LabelComponentForModalRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: MessageComponentTypes
    id: Annotated[int | None, Field(ge=0)] = None
    label: Annotated[str, Field(max_length=45, min_length=1)]
    description: Annotated[str | None, Field(max_length=100, min_length=1)] = None
    component: (
        ChannelSelectComponentForModalRequest
        | CheckboxComponentForModalRequest
        | CheckboxGroupComponentForModalRequest
        | FileUploadComponentForModalRequest
        | MentionableSelectComponentForModalRequest
        | RadioGroupComponentForModalRequest
        | RoleSelectComponentForModalRequest
        | StringSelectComponentForModalRequest
        | TextInputComponentForModalRequest
        | UserSelectComponentForModalRequest
    )
