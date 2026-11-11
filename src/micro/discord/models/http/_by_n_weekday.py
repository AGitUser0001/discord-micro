# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._recurrence_rule_weekdays import RecurrenceRuleWeekdays


class ByNWeekday(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    n: Annotated[
        int,
        Field(
            description='The week to reoccur on (1-5, where 5 represents the last week)',
            ge=1,
            le=5,
        ),
    ]
    day: Annotated[
        RecurrenceRuleWeekdays,
        Field(description='The day within the week to reoccur on'),
    ]
