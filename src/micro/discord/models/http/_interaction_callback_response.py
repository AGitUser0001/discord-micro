# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._launch_activity_interaction_callback_response import LaunchActivityInteractionCallbackResponse
from ._interaction_response import InteractionResponse
from ._update_message_interaction_callback_response import UpdateMessageInteractionCallbackResponse
from ._create_message_interaction_callback_response import CreateMessageInteractionCallbackResponse


class InteractionCallbackResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    interaction: InteractionResponse
    resource: (
        CreateMessageInteractionCallbackResponse
        | LaunchActivityInteractionCallbackResponse
        | UpdateMessageInteractionCallbackResponse
        | None
    ) = None
