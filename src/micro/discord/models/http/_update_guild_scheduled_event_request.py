# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._stage_scheduled_event_patch_request_partial import StageScheduledEventPatchRequestPartial
from ._voice_scheduled_event_patch_request_partial import VoiceScheduledEventPatchRequestPartial
from ._external_scheduled_event_patch_request_partial import ExternalScheduledEventPatchRequestPartial


class UpdateGuildScheduledEventRequest(
    RootModel[
        ExternalScheduledEventPatchRequestPartial
        | StageScheduledEventPatchRequestPartial
        | VoiceScheduledEventPatchRequestPartial
    ]
):
    root: (
        ExternalScheduledEventPatchRequestPartial
        | StageScheduledEventPatchRequestPartial
        | VoiceScheduledEventPatchRequestPartial
    )
