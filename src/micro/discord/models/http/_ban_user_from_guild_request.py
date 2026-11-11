# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class BanUserFromGuildRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    delete_message_seconds: Annotated[int | None, Field(ge=0, le=604800)] = None
    delete_message_days: Annotated[int | None, Field(ge=0, le=7)] = None
