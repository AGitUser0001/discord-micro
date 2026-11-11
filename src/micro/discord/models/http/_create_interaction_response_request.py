# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._launch_activity_interaction_callback_request import LaunchActivityInteractionCallbackRequest
from ._pong_interaction_callback_request import PongInteractionCallbackRequest
from ._social_layer_sku_purchase_eligibility_interaction_callback_request import SocialLayerSKUPurchaseEligibilityInteractionCallbackRequest
from ._application_command_autocomplete_callback_request import ApplicationCommandAutocompleteCallbackRequest
from ._update_message_interaction_callback_request import UpdateMessageInteractionCallbackRequest
from ._create_message_interaction_callback_request import CreateMessageInteractionCallbackRequest
from ._modal_interaction_callback_request import ModalInteractionCallbackRequest


class CreateInteractionResponseRequest(
    RootModel[
        ApplicationCommandAutocompleteCallbackRequest
        | CreateMessageInteractionCallbackRequest
        | LaunchActivityInteractionCallbackRequest
        | ModalInteractionCallbackRequest
        | PongInteractionCallbackRequest
        | SocialLayerSKUPurchaseEligibilityInteractionCallbackRequest
        | UpdateMessageInteractionCallbackRequest
    ]
):
    root: (
        ApplicationCommandAutocompleteCallbackRequest
        | CreateMessageInteractionCallbackRequest
        | LaunchActivityInteractionCallbackRequest
        | ModalInteractionCallbackRequest
        | PongInteractionCallbackRequest
        | SocialLayerSKUPurchaseEligibilityInteractionCallbackRequest
        | UpdateMessageInteractionCallbackRequest
    )
