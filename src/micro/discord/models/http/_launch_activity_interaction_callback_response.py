# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._activity_instance_callback_response import ActivityInstanceCallbackResponse
from ._interaction_callback_types import InteractionCallbackTypes


class LaunchActivityInteractionCallbackResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: InteractionCallbackTypes
    activity_instance: ActivityInstanceCallbackResponse
