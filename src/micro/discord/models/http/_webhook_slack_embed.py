# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._webhook_slack_embed_field import WebhookSlackEmbedField


class WebhookSlackEmbed(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    title: Annotated[str | None, Field(max_length=152133)] = None
    title_link: AnyUrl | None = None
    text: Annotated[str | None, Field(max_length=152133)] = None
    color: Annotated[
        str | None,
        Field(max_length=7, pattern='^#(([0-9a-fA-F]{2}){3}|([0-9a-fA-F]){3})$'),
    ] = None
    ts: int | None = None
    pretext: Annotated[str | None, Field(max_length=152133)] = None
    footer: Annotated[str | None, Field(max_length=152133)] = None
    footer_icon: AnyUrl | None = None
    author_name: Annotated[str | None, Field(max_length=152133)] = None
    author_link: AnyUrl | None = None
    author_icon: AnyUrl | None = None
    image_url: AnyUrl | None = None
    thumb_url: AnyUrl | None = None
    fields: Annotated[list[WebhookSlackEmbedField] | None, Field(max_length=1521)] = (
        None
    )
