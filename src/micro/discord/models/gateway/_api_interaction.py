# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_application_command_autocomplete_interaction import APIApplicationCommandAutocompleteInteraction
from ._api_chat_input_application_command_interaction import APIChatInputApplicationCommandInteraction
from ._api_message_component_interaction import APIMessageComponentInteraction
from ._api_modal_submit_interaction import APIModalSubmitInteraction
from ._api_primary_entry_point_command_interaction import APIPrimaryEntryPointCommandInteraction
from ._api_user_application_command_interaction import APIUserApplicationCommandInteraction
from ._api_ping_interaction import APIPingInteraction
from ._api_message_application_command_interaction import APIMessageApplicationCommandInteraction


class APIInteraction(
    RootModel[
        APIPingInteraction
        | APIApplicationCommandAutocompleteInteraction
        | APIChatInputApplicationCommandInteraction
        | APIMessageApplicationCommandInteraction
        | APIMessageComponentInteraction
        | APIModalSubmitInteraction
        | APIPrimaryEntryPointCommandInteraction
        | APIUserApplicationCommandInteraction
    ]
):
    root: (
        APIPingInteraction
        | APIApplicationCommandAutocompleteInteraction
        | APIChatInputApplicationCommandInteraction
        | APIMessageApplicationCommandInteraction
        | APIMessageComponentInteraction
        | APIModalSubmitInteraction
        | APIPrimaryEntryPointCommandInteraction
        | APIUserApplicationCommandInteraction
    )
