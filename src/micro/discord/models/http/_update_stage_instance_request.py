# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._stage_instances_privacy_levels import StageInstancesPrivacyLevels


class UpdateStageInstanceRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    topic: Annotated[str | None, Field(max_length=120, min_length=1)] = None
    privacy_level: StageInstancesPrivacyLevels | None = None
