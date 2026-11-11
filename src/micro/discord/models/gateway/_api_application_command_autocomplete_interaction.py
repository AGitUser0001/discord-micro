# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_entitlement import APIEntitlement
from ._guild_locale import GuildLocale
from ._context import Context
from ._locale import Locale
from ._api_partial_interaction_guild import APIPartialInteractionGuild
from ._partial_api_guild_category_channel_pick_api_channelidtype import PartialAPIGuildCategoryChannelPickAPIChannelidtype
from ._partial_api_guild_forum_channel_pick_api_channelidtype import PartialAPIGuildForumChannelPickAPIChannelidtype
from ._partial_api_guild_media_channel_pick_api_channelidtype import PartialAPIGuildMediaChannelPickAPIChannelidtype
from ._partial_api_guild_voice_channel_pick_api_channelidtype import PartialAPIGuildVoiceChannelPickAPIChannelidtype
from ._partial_api_guild_stage_voice_channel_pick_api_channelidtype import PartialAPIGuildStageVoiceChannelPickAPIChannelidtype
from ._partial_api_news_channel_pick_api_channelidtype import PartialAPINewsChannelPickAPIChannelidtype
from ._partial_api_text_channel_pick_api_channelidtype import PartialAPITextChannelPickAPIChannelidtype
from ._api_authorizing_integration_owners_map import APIAuthorizingIntegrationOwnersMap
from ._api_user import APIUser
from ._partial_api_announcement_thread_channel_pick_api_channelidtype import PartialAPIAnnouncementThreadChannelPickAPIChannelidtype
from ._partial_apidm_channel_pick_api_channelidtype import PartialAPIDMChannelPickAPIChannelidtype
from ._partial_api_group_dm_channel_pick_api_channelidtype import PartialAPIGroupDMChannelPickAPIChannelidtype
from ._partial_api_public_thread_channel_pick_api_channelidtype import PartialAPIPublicThreadChannelPickAPIChannelidtype
from ._partial_api_private_thread_channel_pick_api_channelidtype import PartialAPIPrivateThreadChannelPickAPIChannelidtype
from ._api_interaction_guild_member import APIInteractionGuildMember
from ._api_autocomplete_application_command_interaction_data_required_pick_api_autocomplete_application_command_interaction_dataoptions import APIAutocompleteApplicationCommandInteractionDataRequiredPickAPIAutocompleteApplicationCommandInteractionDataoptions
from ._api_message import APIMessage


class APIApplicationCommandAutocompleteInteraction(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: Annotated[str, Field(description='ID of the interaction')]
    application_id: Annotated[
        str, Field(description='ID of the application this interaction is for')
    ]
    type: Annotated[Literal[4], Field(description='The type of interaction')]
    data: Annotated[
        APIAutocompleteApplicationCommandInteractionDataRequiredPickAPIAutocompleteApplicationCommandInteractionDataoptions,
        Field(description='The command data payload'),
    ]
    guild: Annotated[
        APIPartialInteractionGuild | None,
        Field(description='Guild that the interaction was sent from'),
    ] = None
    guild_id: Annotated[
        str | None, Field(description='Guild that the interaction was sent from')
    ] = None
    channel: Annotated[
        PartialAPIAnnouncementThreadChannelPickAPIChannelidtype
        | PartialAPIDMChannelPickAPIChannelidtype
        | PartialAPIGroupDMChannelPickAPIChannelidtype
        | PartialAPIGuildCategoryChannelPickAPIChannelidtype
        | PartialAPIGuildForumChannelPickAPIChannelidtype
        | PartialAPIGuildMediaChannelPickAPIChannelidtype
        | PartialAPIGuildVoiceChannelPickAPIChannelidtype
        | PartialAPIGuildStageVoiceChannelPickAPIChannelidtype
        | PartialAPINewsChannelPickAPIChannelidtype
        | PartialAPIPublicThreadChannelPickAPIChannelidtype
        | PartialAPIPrivateThreadChannelPickAPIChannelidtype
        | PartialAPITextChannelPickAPIChannelidtype
        | None,
        Field(description='The channel it was sent from', discriminator='type'),
    ] = None
    channel_id: Annotated[
        str | None,
        Field(deprecated=True, description='The id of the channel it was sent from'),
    ] = None
    member: Annotated[
        APIInteractionGuildMember | None,
        Field(
            description='Guild member data for the invoking user, including permissions\n\n**This is only sent when an interaction is invoked in a guild**'
        ),
    ] = None
    user: Annotated[
        APIUser | None,
        Field(description='User object for the invoking user, if invoked in a DM'),
    ] = None
    token: Annotated[
        str, Field(description='A continuation token for responding to the interaction')
    ]
    version: Annotated[Literal[1], Field(description='Read-only property, always `1`')]
    message: Annotated[
        APIMessage | None,
        Field(description='For components, the message they were attached to'),
    ] = None
    app_permissions: Annotated[
        str,
        Field(
            description='Bitwise set of permissions the app or bot has within the channel the interaction was sent from'
        ),
    ]
    locale: Annotated[
        Locale, Field(description='The selected language of the invoking user')
    ]
    guild_locale: Annotated[
        GuildLocale | None,
        Field(description="The guild's preferred locale, if invoked in a guild"),
    ] = None
    entitlements: Annotated[
        list[APIEntitlement],
        Field(
            description='For monetized apps, any entitlements for the invoking user, representing access to premium SKUs'
        ),
    ]
    authorizing_integration_owners: Annotated[
        APIAuthorizingIntegrationOwnersMap,
        Field(
            description='Mapping of installation contexts that the interaction was authorized for to related user or guild IDs.'
        ),
    ]
    context: Annotated[
        Context | None,
        Field(description='Context where the interaction was triggered from'),
    ] = None
    attachment_size_limit: Annotated[
        float, Field(description='Attachment size limit in bytes')
    ]
