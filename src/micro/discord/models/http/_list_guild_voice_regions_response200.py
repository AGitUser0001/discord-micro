# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._voice_region_response import VoiceRegionResponse


class ListGuildVoiceRegionsResponse200(RootModel[list[VoiceRegionResponse] | None]):
    root: list[VoiceRegionResponse] | None
