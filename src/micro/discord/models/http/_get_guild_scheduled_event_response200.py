# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._stage_scheduled_event_response import StageScheduledEventResponse
from ._voice_scheduled_event_response import VoiceScheduledEventResponse
from ._external_scheduled_event_response import ExternalScheduledEventResponse


class GetGuildScheduledEventResponse200(
    RootModel[
        ExternalScheduledEventResponse
        | StageScheduledEventResponse
        | VoiceScheduledEventResponse
    ]
):
    root: (
        ExternalScheduledEventResponse
        | StageScheduledEventResponse
        | VoiceScheduledEventResponse
    )
