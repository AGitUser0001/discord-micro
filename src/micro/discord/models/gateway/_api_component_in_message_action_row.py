# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_button_component_with_custom_id import APIButtonComponentWithCustomId
from ._api_button_component_with_sku_id import APIButtonComponentWithSKUId
from ._api_button_component_with_url import APIButtonComponentWithURL
from ._api_channel_select_component import APIChannelSelectComponent
from ._api_string_select_component import APIStringSelectComponent
from ._api_mentionable_select_component import APIMentionableSelectComponent
from ._api_role_select_component import APIRoleSelectComponent
from ._api_user_select_component import APIUserSelectComponent


class APIComponentInMessageActionRow(
    RootModel[
        APIButtonComponentWithCustomId
        | APIButtonComponentWithSKUId
        | APIButtonComponentWithURL
        | APIChannelSelectComponent
        | APIStringSelectComponent
        | APIMentionableSelectComponent
        | APIRoleSelectComponent
        | APIUserSelectComponent
    ]
):
    root: (
        APIButtonComponentWithCustomId
        | APIButtonComponentWithSKUId
        | APIButtonComponentWithURL
        | APIChannelSelectComponent
        | APIStringSelectComponent
        | APIMentionableSelectComponent
        | APIRoleSelectComponent
        | APIUserSelectComponent
    )
