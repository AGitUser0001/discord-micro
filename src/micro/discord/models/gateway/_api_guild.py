# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._afk_timeout import AfkTimeout
from ._verification_level import VerificationLevel
from ._default_message_notifications import DefaultMessageNotifications
from ._explicit_content_filter import ExplicitContentFilter
from ._feature import Feature
from ._mfa_level import MfaLevel
from ._system_channel_flags import SystemChannelFlags
from ._premium_tier import PremiumTier
from ._preferred_locale import PreferredLocale
from ._nsfw_level import NsfwLevel
from ._api_incidents_data import APIIncidentsData
from ._hub_type1 import HubType1
from ._api_guild_welcome_screen import APIGuildWelcomeScreen
from ._api_role import APIRole
from ._api_emoji import APIEmoji
from ._api_sticker import APISticker


class APIGuild(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='Guild id')]
    name: Annotated[
        str,
        Field(
            description='Guild name (2-100 characters, excluding trailing and leading whitespace)'
        ),
    ]
    icon: Annotated[str | None, Field(description='Icon hash')]
    splash: Annotated[str | None, Field(description='Splash hash')]
    welcome_screen: Annotated[
        APIGuildWelcomeScreen | None,
        Field(
            description='The welcome screen of a Community guild, shown to new members\n\nReturned in the invite object'
        ),
    ] = None
    icon_hash: Annotated[
        str | None, Field(description='Icon hash, returned when in the template object')
    ] = None
    discovery_splash: Annotated[
        str | None,
        Field(
            description='Discovery splash hash; only present for guilds with the "DISCOVERABLE" feature'
        ),
    ]
    owner: Annotated[
        bool | None,
        Field(
            description='`true` if the user is the owner of the guild\n\n**This field is only received from https://discord.com/developers/docs/resources/user#get-current-user-guilds**'
        ),
    ] = None
    owner_id: Annotated[str, Field(description='ID of owner')]
    permissions: Annotated[
        str | None,
        Field(
            description='Total permissions for the user in the guild (excludes overrides)\n\n**This field is only received from https://discord.com/developers/docs/resources/user#get-current-user-guilds**'
        ),
    ] = None
    region: Annotated[
        str | None, Field(deprecated=True, description='Voice region id for the guild')
    ] = None
    afk_channel_id: Annotated[str | None, Field(description='ID of afk channel')]
    afk_timeout: Annotated[
        AfkTimeout,
        Field(
            description='afk timeout in seconds, can be set to: `60`, `300`, `900`, `1800`, `3600`'
        ),
    ]
    widget_enabled: Annotated[
        bool | None, Field(description='`true` if the guild widget is enabled')
    ] = None
    widget_channel_id: Annotated[
        str | None,
        Field(
            description='The channel id that the widget will generate an invite to, or `null` if set to no invite'
        ),
    ] = None
    verification_level: Annotated[
        VerificationLevel,
        Field(description='Verification level required for the guild'),
    ]
    default_message_notifications: Annotated[
        DefaultMessageNotifications,
        Field(description='Default message notifications level'),
    ]
    explicit_content_filter: Annotated[
        ExplicitContentFilter, Field(description='Explicit content filter level')
    ]
    roles: Annotated[list[APIRole], Field(description='Roles in the guild')]
    emojis: Annotated[list[APIEmoji], Field(description='Custom guild emojis')]
    features: Annotated[list[Feature], Field(description='Enabled guild features')]
    mfa_level: Annotated[
        MfaLevel, Field(description='Required MFA level for the guild')
    ]
    application_id: Annotated[
        str | None,
        Field(description='Application id of the guild creator if it is bot-created'),
    ]
    system_channel_id: Annotated[
        str | None,
        Field(
            description='The id of the channel where guild notices such as welcome messages and boost events are posted'
        ),
    ]
    system_channel_flags: Annotated[
        SystemChannelFlags, Field(description='System channel flags')
    ]
    rules_channel_id: Annotated[
        str | None,
        Field(
            description='The id of the channel where Community guilds can display rules and/or guidelines'
        ),
    ]
    max_presences: Annotated[
        float | None,
        Field(
            description='The maximum number of presences for the guild (`null` is always returned, apart from the largest of guilds)'
        ),
    ] = None
    max_members: Annotated[
        float | None, Field(description='The maximum number of members for the guild')
    ] = None
    vanity_url_code: Annotated[
        str | None, Field(description='The vanity url code for the guild')
    ]
    description: Annotated[
        str | None, Field(description='The description for the guild')
    ]
    banner: Annotated[str | None, Field(description='Banner hash')]
    premium_tier: Annotated[
        PremiumTier, Field(description='Premium tier (Server Boost level)')
    ]
    premium_subscription_count: Annotated[
        float | None, Field(description='The number of boosts this guild currently has')
    ] = None
    preferred_locale: Annotated[
        PreferredLocale,
        Field(
            description='The preferred locale of a Community guild; used in guild discovery and notices from Discord'
        ),
    ]
    public_updates_channel_id: Annotated[
        str | None,
        Field(
            description='The id of the channel where admins and moderators of Community guilds receive notices from Discord'
        ),
    ]
    max_video_channel_users: Annotated[
        float | None,
        Field(description='The maximum amount of users in a video channel'),
    ] = None
    max_stage_video_channel_users: Annotated[
        float | None,
        Field(description='The maximum amount of users in a stage video channel'),
    ] = None
    approximate_member_count: Annotated[
        float | None,
        Field(
            description='Approximate number of members in this guild,\nreturned from the `GET /guilds/<id>` and `/users/@me/guilds` (OAuth2) endpoints when `with_counts` is `true`'
        ),
    ] = None
    approximate_presence_count: Annotated[
        float | None,
        Field(
            description='Approximate number of non-offline members in this guild,\nreturned from the `GET /guilds/<id>` and `/users/@me/guilds` (OAuth2) endpoints when `with_counts` is `true`'
        ),
    ] = None
    nsfw_level: Annotated[NsfwLevel, Field(description='The nsfw level of the guild')]
    stickers: Annotated[
        list[APISticker] | None, Field(description='Custom guild stickers')
    ] = None
    premium_progress_bar_enabled: Annotated[
        bool, Field(description='Whether the guild has the boost progress bar enabled.')
    ]
    hub_type: Annotated[
        HubType1 | None, Field(description='The type of Student Hub the guild is')
    ]
    safety_alerts_channel_id: Annotated[
        str | None,
        Field(
            description='The id of the channel where admins and moderators of Community guilds receive safety alerts from Discord'
        ),
    ]
    incidents_data: Annotated[
        APIIncidentsData | None, Field(description='The incidents data for this guild')
    ]
