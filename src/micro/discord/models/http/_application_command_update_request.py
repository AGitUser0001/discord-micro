# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_handler import ApplicationCommandHandler
from ._application_command_role_option import ApplicationCommandRoleOption
from ._application_command_string_option import ApplicationCommandStringOption
from ._application_command_type import ApplicationCommandType
from ._application_command_user_option import ApplicationCommandUserOption
from ._application_integration_type import ApplicationIntegrationType
from ._interaction_context_type import InteractionContextType
from ._snowflake_type import SnowflakeType
from ._application_command_attachment_option import ApplicationCommandAttachmentOption
from ._application_command_boolean_option import ApplicationCommandBooleanOption
from ._application_command_channel_option import ApplicationCommandChannelOption
from ._application_command_mentionable_option import ApplicationCommandMentionableOption
from ._application_command_number_option import ApplicationCommandNumberOption
from ._application_command_integer_option import ApplicationCommandIntegerOption
from ._application_command_subcommand_option import ApplicationCommandSubcommandOption
from ._application_command_subcommand_group_option import ApplicationCommandSubcommandGroupOption


class ApplicationCommandUpdateRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    name: Annotated[str, Field(max_length=32, min_length=1)]
    name_localizations: dict[str, Any] | None = None
    description: Annotated[str | None, Field(max_length=100)] = None
    description_localizations: dict[str, Any] | None = None
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
            | ApplicationCommandSubcommandGroupOption
            | ApplicationCommandSubcommandOption
            | ApplicationCommandUserOption
        ]
        | None,
        Field(max_length=25),
    ] = None
    default_member_permissions: Annotated[
        int | None, Field(ge=0, le=18014398509481983)
    ] = None
    dm_permission: bool | None = None
    contexts: Annotated[list[InteractionContextType] | None, Field(min_length=1)] = None
    integration_types: Annotated[
        list[ApplicationIntegrationType] | None, Field(min_length=1)
    ] = None
    handler: Annotated[
        ApplicationCommandHandler | None,
        Field(
            description="Determines whether the interaction is handled by the app's interactions handler or by Discord"
        ),
    ] = None
    type: ApplicationCommandType | None = None
    id: SnowflakeType | None = None
