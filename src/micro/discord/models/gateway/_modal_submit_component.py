# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_modal_submit_text_input_component import APIModalSubmitTextInputComponent
from ._api_modal_submit_channel_select_component import APIModalSubmitChannelSelectComponent
from ._api_modal_submit_checkbox_component import APIModalSubmitCheckboxComponent
from ._api_modal_submit_checkbox_group_component import APIModalSubmitCheckboxGroupComponent
from ._api_modal_submit_file_upload_component import APIModalSubmitFileUploadComponent
from ._api_modal_submit_mentionable_select_component import APIModalSubmitMentionableSelectComponent
from ._api_modal_submit_radio_group_component import APIModalSubmitRadioGroupComponent
from ._api_modal_submit_role_select_component import APIModalSubmitRoleSelectComponent
from ._api_modal_submit_string_select_component import APIModalSubmitStringSelectComponent
from ._api_modal_submit_user_select_component import APIModalSubmitUserSelectComponent


class ModalSubmitComponent(
    RootModel[
        APIModalSubmitChannelSelectComponent
        | APIModalSubmitCheckboxComponent
        | APIModalSubmitCheckboxGroupComponent
        | APIModalSubmitFileUploadComponent
        | APIModalSubmitMentionableSelectComponent
        | APIModalSubmitRadioGroupComponent
        | APIModalSubmitRoleSelectComponent
        | APIModalSubmitStringSelectComponent
        | APIModalSubmitTextInputComponent
        | APIModalSubmitUserSelectComponent
    ]
):
    root: Annotated[
        APIModalSubmitChannelSelectComponent
        | APIModalSubmitCheckboxComponent
        | APIModalSubmitCheckboxGroupComponent
        | APIModalSubmitFileUploadComponent
        | APIModalSubmitMentionableSelectComponent
        | APIModalSubmitRadioGroupComponent
        | APIModalSubmitRoleSelectComponent
        | APIModalSubmitStringSelectComponent
        | APIModalSubmitTextInputComponent
        | APIModalSubmitUserSelectComponent,
        Field(discriminator='type'),
    ]
