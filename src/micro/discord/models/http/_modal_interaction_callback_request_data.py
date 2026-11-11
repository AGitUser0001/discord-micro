# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._text_display_component_for_modal_request import TextDisplayComponentForModalRequest
from ._action_row_component_for_modal_request import ActionRowComponentForModalRequest
from ._label_component_for_modal_request import LabelComponentForModalRequest


class ModalInteractionCallbackRequestData(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    custom_id: Annotated[str, Field(max_length=100, min_length=1)]
    title: Annotated[str, Field(max_length=45, min_length=1)]
    components: Annotated[
        list[
            ActionRowComponentForModalRequest
            | LabelComponentForModalRequest
            | TextDisplayComponentForModalRequest
        ],
        Field(max_length=40, min_length=1),
    ]
