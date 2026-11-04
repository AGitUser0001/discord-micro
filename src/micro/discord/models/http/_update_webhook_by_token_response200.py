# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._application_incoming_webhook_response import ApplicationIncomingWebhookResponse
from ._channel_follower_webhook_response import ChannelFollowerWebhookResponse
from ._guild_incoming_webhook_response import GuildIncomingWebhookResponse


class UpdateWebhookByTokenResponse200(
    RootModel[
        ApplicationIncomingWebhookResponse
        | ChannelFollowerWebhookResponse
        | GuildIncomingWebhookResponse
    ]
):
    root: (
        ApplicationIncomingWebhookResponse
        | ChannelFollowerWebhookResponse
        | GuildIncomingWebhookResponse
    )
