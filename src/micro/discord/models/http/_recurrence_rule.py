# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._by_month_day_item import ByMonthDayItem
from ._by_year_day_item import ByYearDayItem
from ._recurrence_rule_frequencies import RecurrenceRuleFrequencies
from ._recurrence_rule_months import RecurrenceRuleMonths
from ._recurrence_rule_weekdays import RecurrenceRuleWeekdays
from ._by_n_weekday import ByNWeekday


class RecurrenceRule(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    start: Annotated[
        AwareDatetime, Field(description='Starting time of the recurrence interval')
    ]
    end: Annotated[
        AwareDatetime | None,
        Field(description='Ending time of the recurrence interval'),
    ] = None
    frequency: Annotated[
        RecurrenceRuleFrequencies, Field(description='How often the event occurs')
    ]
    interval: Annotated[
        int | None,
        Field(description='The spacing between events, defined by frequency'),
    ] = None
    by_weekday: Annotated[
        list[RecurrenceRuleWeekdays] | None,
        Field(
            description='Set of specific days within a week for the event to recur on',
            max_length=7,
        ),
    ] = None
    by_n_weekday: Annotated[
        list[ByNWeekday] | None,
        Field(
            description='List of specific days within a specific week to recur on',
            max_length=7,
        ),
    ] = None
    by_month: Annotated[
        list[RecurrenceRuleMonths] | None,
        Field(description='Set of specific months to recur on', max_length=12),
    ] = None
    by_month_day: Annotated[
        list[ByMonthDayItem] | None,
        Field(
            description='Set of specific dates within a month to recur on',
            max_length=33,
        ),
    ] = None
    by_year_day: Annotated[
        list[ByYearDayItem] | None,
        Field(
            description='Set of days within a year to recur on (1-364)', max_length=367
        ),
    ] = None
    count: Annotated[
        int | None,
        Field(description='Total number of times the event is allowed to recur'),
    ] = None
