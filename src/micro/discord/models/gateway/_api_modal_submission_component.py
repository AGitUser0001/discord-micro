# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._modal_submit_text_display_component import ModalSubmitTextDisplayComponent
from ._modal_submit_action_row_component import ModalSubmitActionRowComponent
from ._modal_submit_label_component import ModalSubmitLabelComponent


class APIModalSubmissionComponent(
    RootModel[
        ModalSubmitActionRowComponent
        | ModalSubmitLabelComponent
        | ModalSubmitTextDisplayComponent
    ]
):
    root: Annotated[
        ModalSubmitActionRowComponent
        | ModalSubmitLabelComponent
        | ModalSubmitTextDisplayComponent,
        Field(discriminator='type'),
    ]
