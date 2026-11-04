# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._audit_log_entry_response import AuditLogEntryResponse
from ._keyword_rule_response import KeywordRuleResponse
from ._ml_spam_rule_response import MLSpamRuleResponse
from ._mention_spam_rule_response import MentionSpamRuleResponse
from ._partial_discord_integration_response import PartialDiscordIntegrationResponse
from ._partial_external_connection_integration_response import PartialExternalConnectionIntegrationResponse
from ._partial_guild_subscription_integration_response import PartialGuildSubscriptionIntegrationResponse
from ._user_profile_rule_response import UserProfileRuleResponse
from ._user_response import UserResponse
from ._application_incoming_webhook_response import ApplicationIncomingWebhookResponse
from ._channel_follower_webhook_response import ChannelFollowerWebhookResponse
from ._default_keyword_rule_response import DefaultKeywordRuleResponse
from ._guild_incoming_webhook_response import GuildIncomingWebhookResponse
from ._stage_scheduled_event_response import StageScheduledEventResponse
from ._thread_response import ThreadResponse
from ._voice_scheduled_event_response import VoiceScheduledEventResponse
from ._external_scheduled_event_response import ExternalScheduledEventResponse
from ._application_command_response import ApplicationCommandResponse


class GuildAuditLogResponse(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    audit_log_entries: list[AuditLogEntryResponse]
    users: list[UserResponse]
    integrations: list[
        PartialDiscordIntegrationResponse
        | PartialExternalConnectionIntegrationResponse
        | PartialGuildSubscriptionIntegrationResponse
    ]
    webhooks: list[
        ApplicationIncomingWebhookResponse
        | ChannelFollowerWebhookResponse
        | GuildIncomingWebhookResponse
    ]
    guild_scheduled_events: list[
        ExternalScheduledEventResponse
        | StageScheduledEventResponse
        | VoiceScheduledEventResponse
    ]
    threads: list[ThreadResponse]
    application_commands: list[ApplicationCommandResponse]
    auto_moderation_rules: list[
        DefaultKeywordRuleResponse
        | KeywordRuleResponse
        | MLSpamRuleResponse
        | MentionSpamRuleResponse
        | UserProfileRuleResponse
        | None
    ]
