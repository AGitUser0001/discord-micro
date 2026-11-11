# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._scheduled_event_user_response import ScheduledEventUserResponse


class ListGuildScheduledEventExceptionUsersResponse200(
    RootModel[list[ScheduledEventUserResponse] | None]
):
    root: list[ScheduledEventUserResponse] | None
