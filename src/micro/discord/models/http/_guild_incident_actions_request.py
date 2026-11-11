# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class GuildIncidentActionsRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    invites_disabled_until: Annotated[
        AwareDatetime | None, Field(description='When invites will be enabled again')
    ] = None
    dms_disabled_until: Annotated[
        AwareDatetime | None,
        Field(description='When direct messages will be enabled again'),
    ] = None
