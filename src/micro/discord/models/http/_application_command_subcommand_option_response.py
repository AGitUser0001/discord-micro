# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_option_type import ApplicationCommandOptionType
from ._application_command_role_option_response import ApplicationCommandRoleOptionResponse
from ._application_command_string_option_response import ApplicationCommandStringOptionResponse
from ._application_command_user_option_response import ApplicationCommandUserOptionResponse
from ._application_command_attachment_option_response import ApplicationCommandAttachmentOptionResponse
from ._application_command_boolean_option_response import ApplicationCommandBooleanOptionResponse
from ._application_command_channel_option_response import ApplicationCommandChannelOptionResponse
from ._application_command_mentionable_option_response import ApplicationCommandMentionableOptionResponse
from ._application_command_number_option_response import ApplicationCommandNumberOptionResponse
from ._application_command_integer_option_response import ApplicationCommandIntegerOptionResponse


class ApplicationCommandSubcommandOptionResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: ApplicationCommandOptionType
    name: str
    name_localized: str | None = None
    name_localizations: dict[str, Any] | None = None
    description: str
    description_localized: str | None = None
    description_localizations: dict[str, Any] | None = None
    required: bool | None = None
    options: (
        list[
            ApplicationCommandAttachmentOptionResponse
            | ApplicationCommandBooleanOptionResponse
            | ApplicationCommandChannelOptionResponse
            | ApplicationCommandIntegerOptionResponse
            | ApplicationCommandMentionableOptionResponse
            | ApplicationCommandNumberOptionResponse
            | ApplicationCommandRoleOptionResponse
            | ApplicationCommandStringOptionResponse
            | ApplicationCommandUserOptionResponse
        ]
        | None
    ) = None
