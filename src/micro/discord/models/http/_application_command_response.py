# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_command_handler import ApplicationCommandHandler
from ._application_command_role_option_response import ApplicationCommandRoleOptionResponse
from ._application_command_string_option_response import ApplicationCommandStringOptionResponse
from ._application_command_type import ApplicationCommandType
from ._application_command_user_option_response import ApplicationCommandUserOptionResponse
from ._application_integration_type import ApplicationIntegrationType
from ._interaction_context_type import InteractionContextType
from ._snowflake_type import SnowflakeType
from ._application_command_attachment_option_response import ApplicationCommandAttachmentOptionResponse
from ._application_command_boolean_option_response import ApplicationCommandBooleanOptionResponse
from ._application_command_channel_option_response import ApplicationCommandChannelOptionResponse
from ._application_command_mentionable_option_response import ApplicationCommandMentionableOptionResponse
from ._application_command_number_option_response import ApplicationCommandNumberOptionResponse
from ._application_command_integer_option_response import ApplicationCommandIntegerOptionResponse
from ._application_command_subcommand_option_response import ApplicationCommandSubcommandOptionResponse
from ._application_command_subcommand_group_option_response import ApplicationCommandSubcommandGroupOptionResponse


class ApplicationCommandResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: SnowflakeType
    application_id: SnowflakeType
    version: SnowflakeType
    default_member_permissions: str | None
    type: ApplicationCommandType
    name: str
    name_localized: str | None = None
    name_localizations: dict[str, Any] | None = None
    description: str
    description_localized: str | None = None
    description_localizations: dict[str, Any] | None = None
    guild_id: SnowflakeType | None = None
    dm_permission: bool | None = None
    contexts: list[InteractionContextType] | None = None
    integration_types: list[ApplicationIntegrationType] | None = None
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
            | ApplicationCommandSubcommandGroupOptionResponse
            | ApplicationCommandSubcommandOptionResponse
            | ApplicationCommandUserOptionResponse
        ]
        | None
    ) = None
    nsfw: bool | None = None
    handler: Annotated[
        ApplicationCommandHandler | None,
        Field(
            description="Determines whether the interaction is handled by the app's interactions handler or by Discord"
        ),
    ] = None
