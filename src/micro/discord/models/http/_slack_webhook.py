# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._webhook_slack_embed import WebhookSlackEmbed


class SlackWebhook(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    text: Annotated[str | None, Field(max_length=2000)] = None
    username: Annotated[str | None, Field(max_length=152133)] = None
    icon_url: AnyUrl | None = None
    attachments: Annotated[list[WebhookSlackEmbed] | None, Field(max_length=1521)] = (
        None
    )
