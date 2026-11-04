# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._type6 import Type6
from ._status_display_type import StatusDisplayType
from ._flags21 import Flags21
from ._gateway_activity_timestamps import GatewayActivityTimestamps
from ._gateway_activity_emoji import GatewayActivityEmoji
from ._gateway_activity_party import GatewayActivityParty
from ._gateway_activity_assets import GatewayActivityAssets
from ._gateway_activity_secrets import GatewayActivitySecrets
from ._gateway_activity_button import GatewayActivityButton


class GatewayActivity(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description="The activity's id")]
    name: Annotated[str, Field(description="The activity's name")]
    type: Annotated[Type6, Field(description='Activity type')]
    url: Annotated[
        str | None, Field(description='Stream url, is validated when type is `1`')
    ] = None
    created_at: Annotated[
        float,
        Field(
            description="Unix timestamp of when the activity was added to the user's session"
        ),
    ]
    timestamps: Annotated[
        GatewayActivityTimestamps | None,
        Field(description='Unix timestamps for start and/or end of the game'),
    ] = None
    sync_id: Annotated[str | None, Field(description='The Spotify song id')] = None
    platform: Annotated[
        str | None, Field(description='The platform this activity is being done on')
    ] = None
    application_id: Annotated[
        str | None, Field(description='Application id for the game')
    ] = None
    status_display_type: Annotated[
        StatusDisplayType | None,
        Field(
            description="Controls which field is displayed in the user's status text in the member list"
        ),
    ] = None
    details: Annotated[
        str | None, Field(description='What the player is currently doing')
    ] = None
    details_url: Annotated[
        str | None,
        Field(description='URL that is linked when clicking on the details text'),
    ] = None
    state: Annotated[
        str | None,
        Field(
            description="The user's current party status, or the text used for a custom status"
        ),
    ] = None
    state_url: Annotated[
        str | None,
        Field(description='URL that is linked when clicking on the state text'),
    ] = None
    emoji: Annotated[
        GatewayActivityEmoji | None,
        Field(description='The emoji used for a custom status'),
    ] = None
    session_id: str | None = None
    party: Annotated[
        GatewayActivityParty | None,
        Field(description='Information for the current party of the player'),
    ] = None
    assets: Annotated[
        GatewayActivityAssets | None,
        Field(description='Images for the presence and their hover texts'),
    ] = None
    secrets: Annotated[
        GatewayActivitySecrets | None,
        Field(description='Secrets for Rich Presence joining and spectating'),
    ] = None
    instance: Annotated[
        bool | None,
        Field(description='Whether or not the activity is an instanced game session'),
    ] = None
    flags: Annotated[
        Flags21 | None,
        Field(
            description='Activity flags `OR`d together, describes what the payload includes'
        ),
    ] = None
    buttons: Annotated[
        list[str] | list[GatewayActivityButton] | None,
        Field(description='The custom buttons shown in the Rich Presence (max 2)'),
    ] = None
