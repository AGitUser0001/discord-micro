# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_option_type import ApplicationCommandOptionType
from ._application_command_role_option import ApplicationCommandRoleOption
from ._application_command_string_option import ApplicationCommandStringOption
from ._application_command_user_option import ApplicationCommandUserOption
from ._application_command_attachment_option import ApplicationCommandAttachmentOption
from ._application_command_boolean_option import ApplicationCommandBooleanOption
from ._application_command_channel_option import ApplicationCommandChannelOption
from ._application_command_mentionable_option import ApplicationCommandMentionableOption
from ._application_command_number_option import ApplicationCommandNumberOption
from ._application_command_integer_option import ApplicationCommandIntegerOption


class ApplicationCommandSubcommandOption(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: ApplicationCommandOptionType
    name: Annotated[str, Field(max_length=32, min_length=1)]
    name_localizations: dict[str, Any] | None = None
    description: Annotated[str, Field(max_length=100, min_length=1)]
    description_localizations: dict[str, Any] | None = None
    required: bool | None = None
    options: Annotated[
        list[
            ApplicationCommandAttachmentOption
            | ApplicationCommandBooleanOption
            | ApplicationCommandChannelOption
            | ApplicationCommandIntegerOption
            | ApplicationCommandMentionableOption
            | ApplicationCommandNumberOption
            | ApplicationCommandRoleOption
            | ApplicationCommandStringOption
            | ApplicationCommandUserOption
        ]
        | None,
        Field(max_length=25),
    ] = None
