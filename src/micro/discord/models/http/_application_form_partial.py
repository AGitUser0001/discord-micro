# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._action_types import ActionTypes
from ._application_event_webhooks_status import ApplicationEventWebhooksStatus
from ._application_explicit_content_filter_types import ApplicationExplicitContentFilterTypes
from ._description import Description
from ._tag import Tag
from ._application_types import ApplicationTypes
from ._snowflake_type import SnowflakeType
from ._application_o_auth2_install_params import ApplicationOAuth2InstallParams


class ApplicationFormPartial(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    description: Description | None = None
    icon: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    cover_image: Annotated[
        str | None, Field(json_schema_extra={'contentEncoding': 'base64'})
    ] = None
    team_id: SnowflakeType | None = None
    flags: int | None = None
    interactions_endpoint_url: AnyUrl | None = None
    explicit_content_filter: ApplicationExplicitContentFilterTypes | None = None
    max_participants: Annotated[int | None, Field(ge=-1)] = None
    type: ApplicationTypes | None = None
    tags: Annotated[list[Tag] | None, Field(max_length=5)] = None
    custom_install_url: AnyUrl | None = None
    install_params: ApplicationOAuth2InstallParams | None = None
    role_connections_verification_url: AnyUrl | None = None
    integration_types_config: dict[str, Any] | None = None
    event_webhooks_status: ApplicationEventWebhooksStatus | None = None
    event_webhooks_url: Annotated[
        AnyUrl | None,
        Field(description='Event webhooks URL for the app to receive webhook events'),
    ] = None
    event_webhooks_types: list[ActionTypes] | None = None
