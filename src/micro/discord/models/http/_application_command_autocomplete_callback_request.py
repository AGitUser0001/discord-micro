# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._interaction_application_command_autocomplete_callback_number_data import InteractionApplicationCommandAutocompleteCallbackNumberData
from ._interaction_application_command_autocomplete_callback_string_data import InteractionApplicationCommandAutocompleteCallbackStringData
from ._interaction_callback_types import InteractionCallbackTypes
from ._interaction_application_command_autocomplete_callback_integer_data import InteractionApplicationCommandAutocompleteCallbackIntegerData


class ApplicationCommandAutocompleteCallbackRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    type: InteractionCallbackTypes
    data: (
        InteractionApplicationCommandAutocompleteCallbackIntegerData
        | InteractionApplicationCommandAutocompleteCallbackNumberData
        | InteractionApplicationCommandAutocompleteCallbackStringData
    )
