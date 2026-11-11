# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._user_response import UserResponse


class ListMessageReactionsByEmojiResponse200(RootModel[list[UserResponse]]):
    root: list[UserResponse]
