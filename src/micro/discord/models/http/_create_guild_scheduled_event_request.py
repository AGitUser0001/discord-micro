# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._stage_scheduled_event_create_request import StageScheduledEventCreateRequest
from ._voice_scheduled_event_create_request import VoiceScheduledEventCreateRequest
from ._external_scheduled_event_create_request import ExternalScheduledEventCreateRequest


class CreateGuildScheduledEventRequest(
    RootModel[
        ExternalScheduledEventCreateRequest
        | StageScheduledEventCreateRequest
        | VoiceScheduledEventCreateRequest
    ]
):
    root: (
        ExternalScheduledEventCreateRequest
        | StageScheduledEventCreateRequest
        | VoiceScheduledEventCreateRequest
    )
