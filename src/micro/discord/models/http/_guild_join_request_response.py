# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_join_request_application_status import GuildJoinRequestApplicationStatus
from ._multiple_choice_form_field_response import MultipleChoiceFormFieldResponse
from ._paragraph_form_field_response import ParagraphFormFieldResponse
from ._snowflake_type import SnowflakeType
from ._terms_form_field_response import TermsFormFieldResponse
from ._text_input_form_field_response import TextInputFormFieldResponse
from ._user_response import UserResponse


class GuildJoinRequestResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    created_at: AwareDatetime
    reviewed_at: AwareDatetime | None
    application_status: GuildJoinRequestApplicationStatus | None
    rejection_reason: Annotated[
        str | None,
        Field(
            description='Reason request was rejected. Only set when application_status is REJECTED'
        ),
    ]
    guild_id: SnowflakeType
    user_id: SnowflakeType
    user: UserResponse | None = None
    form_responses: Annotated[
        list[
            MultipleChoiceFormFieldResponse
            | ParagraphFormFieldResponse
            | TermsFormFieldResponse
            | TextInputFormFieldResponse
        ]
        | None,
        Field(description="Applicant's responses on join request form"),
    ] = None
    actioned_by_user: UserResponse | None = None
