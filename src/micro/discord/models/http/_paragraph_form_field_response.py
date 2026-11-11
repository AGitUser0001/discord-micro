# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._guild_member_verification_form_field_type import GuildMemberVerificationFormFieldType


class ParagraphFormFieldResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    field_type: Annotated[
        GuildMemberVerificationFormFieldType, Field(description='Type of form field')
    ]
    label: Annotated[str | None, Field(description='Label shown above field')] = None
    description: Annotated[
        str | None, Field(description='Optional helper text shown below label')
    ] = None
    required: Annotated[
        bool | None, Field(description='Whether applicant must fill in field')
    ] = None
    placeholder: Annotated[
        str | None, Field(description='Placeholder text shown in empty input')
    ] = None
    response: Annotated[str | None, Field(description="Applicant's text response")] = (
        None
    )
