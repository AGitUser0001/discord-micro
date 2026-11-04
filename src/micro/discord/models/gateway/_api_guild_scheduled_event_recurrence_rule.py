# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._frequency import Frequency
from ._by_weekday_enum import ByWeekdayEnum
from ._by_month_enum import ByMonthEnum
from ._api_guild_scheduled_event_recurrence_rule_n_weekday import APIGuildScheduledEventRecurrenceRuleNWeekday


class APIGuildScheduledEventRecurrenceRule(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    start: Annotated[str, Field(description='Starting time of the recurrence interval')]
    end: Annotated[
        str | None, Field(description='Ending time of the recurrence interval')
    ]
    frequency: Annotated[Frequency, Field(description='How often the event occurs')]
    interval: Annotated[
        float,
        Field(
            description='The spacing between the events, defined by `frequency`.\nFor example, `frequency` of GuildScheduledEventRecurrenceRuleFrequency.Weekly and an `interval` of `2`\nwould be "every-other week"'
        ),
    ]
    by_weekday: Annotated[
        list[ByWeekdayEnum] | None,
        Field(
            description='Set of specific days within a week for the event to recur on'
        ),
    ]
    by_n_weekday: Annotated[
        list[APIGuildScheduledEventRecurrenceRuleNWeekday] | None,
        Field(
            description='List of specific days within a specific week (1-5) to recur on'
        ),
    ]
    by_month: Annotated[
        list[ByMonthEnum] | None,
        Field(description='Set of specific months to recur on'),
    ]
    by_month_day: Annotated[
        list[float] | None,
        Field(description='Set of specific dates within a month to recur on'),
    ]
    by_year_day: Annotated[
        list[float] | None,
        Field(description='Set of days within a year to recur on (1-364)'),
    ]
    count: Annotated[
        float | None,
        Field(
            description='The total amount of times that the event is allowed to recur before stopping'
        ),
    ]
