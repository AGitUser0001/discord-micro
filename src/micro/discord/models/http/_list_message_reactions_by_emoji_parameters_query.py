# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._reaction_types import ReactionTypes
from ._snowflake_type import SnowflakeType


class ListMessageReactionsByEmojiParametersQuery(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    after: SnowflakeType | None = None
    limit: Annotated[int | None, Field(ge=1, le=100)] = None
    type: ReactionTypes | None = None
