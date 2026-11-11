# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._incoming_webhook_request_partial import IncomingWebhookRequestPartial
from ._incoming_webhook_update_request_partial import IncomingWebhookUpdateRequestPartial


class ExecuteWebhookRequest(
    RootModel[IncomingWebhookRequestPartial | IncomingWebhookUpdateRequestPartial]
):
    root: IncomingWebhookRequestPartial | IncomingWebhookUpdateRequestPartial
