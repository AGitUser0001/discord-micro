# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_command_interaction_data_string_option import APIApplicationCommandInteractionDataStringOption
from ._api_application_command_interaction_data_attachment_option import APIApplicationCommandInteractionDataAttachmentOption
from ._api_application_command_interaction_data_boolean_option import APIApplicationCommandInteractionDataBooleanOption
from ._api_application_command_interaction_data_channel_option import APIApplicationCommandInteractionDataChannelOption
from ._api_application_command_interaction_data_mentionable_option import APIApplicationCommandInteractionDataMentionableOption
from ._api_application_command_interaction_data_role_option import APIApplicationCommandInteractionDataRoleOption
from ._api_application_command_interaction_data_user_option import APIApplicationCommandInteractionDataUserOption
from ._api_application_command_interaction_data_integer_option_application_command import APIApplicationCommandInteractionDataIntegerOptionApplicationCommand
from ._api_application_command_interaction_data_number_option_application_command import APIApplicationCommandInteractionDataNumberOptionApplicationCommand
from ._api_application_command_interaction_data_subcommand_option_application_command import APIApplicationCommandInteractionDataSubcommandOptionApplicationCommand
from ._api_application_command_interaction_data_subcommand_group_option_application_command import APIApplicationCommandInteractionDataSubcommandGroupOptionApplicationCommand


class APIApplicationCommandInteractionDataOptionInteractionTypeApplicationCommand(
    RootModel[
        APIApplicationCommandInteractionDataIntegerOptionApplicationCommand
        | APIApplicationCommandInteractionDataNumberOptionApplicationCommand
        | APIApplicationCommandInteractionDataStringOption
        | APIApplicationCommandInteractionDataSubcommandGroupOptionApplicationCommand
        | APIApplicationCommandInteractionDataSubcommandOptionApplicationCommand
        | APIApplicationCommandInteractionDataAttachmentOption
        | APIApplicationCommandInteractionDataBooleanOption
        | APIApplicationCommandInteractionDataChannelOption
        | APIApplicationCommandInteractionDataMentionableOption
        | APIApplicationCommandInteractionDataRoleOption
        | APIApplicationCommandInteractionDataUserOption
    ]
):
    root: Annotated[
        APIApplicationCommandInteractionDataIntegerOptionApplicationCommand
        | APIApplicationCommandInteractionDataNumberOptionApplicationCommand
        | APIApplicationCommandInteractionDataStringOption
        | APIApplicationCommandInteractionDataSubcommandGroupOptionApplicationCommand
        | APIApplicationCommandInteractionDataSubcommandOptionApplicationCommand
        | APIApplicationCommandInteractionDataAttachmentOption
        | APIApplicationCommandInteractionDataBooleanOption
        | APIApplicationCommandInteractionDataChannelOption
        | APIApplicationCommandInteractionDataMentionableOption
        | APIApplicationCommandInteractionDataRoleOption
        | APIApplicationCommandInteractionDataUserOption,
        Field(discriminator='type'),
    ]
