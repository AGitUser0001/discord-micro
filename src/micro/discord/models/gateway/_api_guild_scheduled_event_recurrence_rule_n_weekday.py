# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._n import N
from ._day import Day


class APIGuildScheduledEventRecurrenceRuleNWeekday(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    n: Annotated[N, Field(description='The week to reoccur on.')]
    day: Annotated[Day, Field(description='The day within the week to reoccur on')]
