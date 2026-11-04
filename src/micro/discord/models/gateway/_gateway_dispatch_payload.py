# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._gateway_entitlement_delete_dispatch import GatewayEntitlementDeleteDispatch
from ._gateway_entitlement_update_dispatch import GatewayEntitlementUpdateDispatch
from ._gateway_message_poll_vote_remove_dispatch import GatewayMessagePollVoteRemoveDispatch
from ._gateway_resumed_dispatch import GatewayResumedDispatch
from ._gateway_stage_instance_create_dispatch import GatewayStageInstanceCreateDispatch
from ._gateway_stage_instance_delete_dispatch import GatewayStageInstanceDeleteDispatch
from ._gateway_stage_instance_update_dispatch import GatewayStageInstanceUpdateDispatch
from ._gateway_subscription_delete_dispatch import GatewaySubscriptionDeleteDispatch
from ._gateway_subscription_update_dispatch import GatewaySubscriptionUpdateDispatch
from ._gateway_auto_moderation_rule_delete_dispatch import GatewayAutoModerationRuleDeleteDispatch
from ._gateway_auto_moderation_rule_update_dispatch import GatewayAutoModerationRuleUpdateDispatch
from ._gateway_channel_pins_update_dispatch import GatewayChannelPinsUpdateDispatch
from ._gateway_entitlement_create_dispatch import GatewayEntitlementCreateDispatch
from ._gateway_guild_delete_dispatch import GatewayGuildDeleteDispatch
from ._gateway_guild_integrations_update_dispatch import GatewayGuildIntegrationsUpdateDispatch
from ._gateway_guild_role_delete_dispatch import GatewayGuildRoleDeleteDispatch
from ._gateway_guild_role_update_dispatch import GatewayGuildRoleUpdateDispatch
from ._gateway_guild_scheduled_event_user_add_dispatch import GatewayGuildScheduledEventUserAddDispatch
from ._gateway_guild_scheduled_event_user_remove_dispatch import GatewayGuildScheduledEventUserRemoveDispatch
from ._gateway_guild_soundboard_sound_delete_dispatch import GatewayGuildSoundboardSoundDeleteDispatch
from ._gateway_integration_delete_dispatch import GatewayIntegrationDeleteDispatch
from ._gateway_invite_delete_dispatch import GatewayInviteDeleteDispatch
from ._gateway_message_delete_bulk_dispatch import GatewayMessageDeleteBulkDispatch
from ._gateway_message_delete_dispatch import GatewayMessageDeleteDispatch
from ._gateway_message_poll_vote_add_dispatch import GatewayMessagePollVoteAddDispatch
from ._gateway_message_reaction_remove_all_dispatch import GatewayMessageReactionRemoveAllDispatch
from ._gateway_subscription_create_dispatch import GatewaySubscriptionCreateDispatch
from ._gateway_thread_delete_dispatch import GatewayThreadDeleteDispatch
from ._gateway_voice_channel_start_time_update_dispatch import GatewayVoiceChannelStartTimeUpdateDispatch
from ._gateway_voice_channel_status_update_dispatch import GatewayVoiceChannelStatusUpdateDispatch
from ._gateway_voice_server_update_dispatch import GatewayVoiceServerUpdateDispatch
from ._gateway_webhooks_update_dispatch import GatewayWebhooksUpdateDispatch
from ._gateway_application_command_permissions_update_dispatch import GatewayApplicationCommandPermissionsUpdateDispatch
from ._gateway_auto_moderation_rule_create_dispatch import GatewayAutoModerationRuleCreateDispatch
from ._gateway_channel_delete_dispatch import GatewayChannelDeleteDispatch
from ._gateway_channel_info_dispatch import GatewayChannelInfoDispatch
from ._gateway_channel_update_dispatch import GatewayChannelUpdateDispatch
from ._gateway_guild_role_create_dispatch import GatewayGuildRoleCreateDispatch
from ._gateway_guild_soundboard_sound_create_dispatch import GatewayGuildSoundboardSoundCreateDispatch
from ._gateway_guild_soundboard_sound_update_dispatch import GatewayGuildSoundboardSoundUpdateDispatch
from ._gateway_presence_update_dispatch import GatewayPresenceUpdateDispatch
from ._gateway_rate_limited_dispatch_gateway_opcodes_request_guild_members import GatewayRateLimitedDispatchGatewayOpcodesRequestGuildMembers
from ._gateway_user_update_dispatch import GatewayUserUpdateDispatch
from ._gateway_auto_moderation_action_execution_dispatch import GatewayAutoModerationActionExecutionDispatch
from ._gateway_channel_create_dispatch import GatewayChannelCreateDispatch
from ._gateway_guild_ban_remove_dispatch import GatewayGuildBanRemoveDispatch
from ._gateway_guild_emojis_update_dispatch import GatewayGuildEmojisUpdateDispatch
from ._gateway_guild_member_add_dispatch import GatewayGuildMemberAddDispatch
from ._gateway_guild_member_remove_dispatch import GatewayGuildMemberRemoveDispatch
from ._gateway_guild_member_update_dispatch import GatewayGuildMemberUpdateDispatch
from ._gateway_guild_members_chunk_dispatch import GatewayGuildMembersChunkDispatch
from ._gateway_guild_modify_dispatch import GatewayGuildModifyDispatch
from ._gateway_guild_scheduled_event_create_dispatch import GatewayGuildScheduledEventCreateDispatch
from ._gateway_guild_scheduled_event_delete_dispatch import GatewayGuildScheduledEventDeleteDispatch
from ._gateway_guild_scheduled_event_update_dispatch import GatewayGuildScheduledEventUpdateDispatch
from ._gateway_guild_soundboard_sounds_update_dispatch import GatewayGuildSoundboardSoundsUpdateDispatch
from ._gateway_guild_stickers_update_dispatch import GatewayGuildStickersUpdateDispatch
from ._gateway_integration_update_dispatch import GatewayIntegrationUpdateDispatch
from ._gateway_message_reaction_add_dispatch import GatewayMessageReactionAddDispatch
from ._gateway_message_reaction_remove_dispatch import GatewayMessageReactionRemoveDispatch
from ._gateway_message_reaction_remove_emoji_dispatch import GatewayMessageReactionRemoveEmojiDispatch
from ._gateway_ready_dispatch import GatewayReadyDispatch
from ._gateway_soundboard_sounds_dispatch import GatewaySoundboardSoundsDispatch
from ._gateway_thread_create_dispatch import GatewayThreadCreateDispatch
from ._gateway_thread_member_update_dispatch import GatewayThreadMemberUpdateDispatch
from ._gateway_thread_members_update_dispatch import GatewayThreadMembersUpdateDispatch
from ._gateway_thread_update_dispatch import GatewayThreadUpdateDispatch
from ._gateway_typing_start_dispatch import GatewayTypingStartDispatch
from ._gateway_voice_channel_effect_send_dispatch import GatewayVoiceChannelEffectSendDispatch
from ._gateway_voice_state_update_dispatch import GatewayVoiceStateUpdateDispatch
from ._gateway_guild_ban_add_dispatch import GatewayGuildBanAddDispatch
from ._gateway_integration_create_dispatch import GatewayIntegrationCreateDispatch
from ._gateway_invite_create_dispatch import GatewayInviteCreateDispatch
from ._gateway_thread_list_sync_dispatch import GatewayThreadListSyncDispatch
from ._gateway_guild_audit_log_entry_create_dispatch import GatewayGuildAuditLogEntryCreateDispatch
from ._gateway_guild_create_dispatch import GatewayGuildCreateDispatch
from ._gateway_message_create_dispatch import GatewayMessageCreateDispatch
from ._gateway_message_update_dispatch import GatewayMessageUpdateDispatch
from ._gateway_interaction_create_dispatch import GatewayInteractionCreateDispatch


class GatewayDispatchPayload(
    RootModel[
        GatewayApplicationCommandPermissionsUpdateDispatch
        | GatewayAutoModerationActionExecutionDispatch
        | GatewayAutoModerationRuleCreateDispatch
        | GatewayAutoModerationRuleDeleteDispatch
        | GatewayAutoModerationRuleUpdateDispatch
        | GatewayChannelCreateDispatch
        | GatewayChannelDeleteDispatch
        | GatewayChannelInfoDispatch
        | GatewayChannelPinsUpdateDispatch
        | GatewayChannelUpdateDispatch
        | GatewayEntitlementCreateDispatch
        | GatewayEntitlementDeleteDispatch
        | GatewayEntitlementUpdateDispatch
        | GatewayGuildAuditLogEntryCreateDispatch
        | GatewayGuildBanAddDispatch
        | GatewayGuildBanRemoveDispatch
        | GatewayGuildCreateDispatch
        | GatewayGuildDeleteDispatch
        | GatewayGuildEmojisUpdateDispatch
        | GatewayGuildIntegrationsUpdateDispatch
        | GatewayGuildMemberAddDispatch
        | GatewayGuildMemberRemoveDispatch
        | GatewayGuildMemberUpdateDispatch
        | GatewayGuildMembersChunkDispatch
        | GatewayGuildModifyDispatch
        | GatewayGuildRoleCreateDispatch
        | GatewayGuildRoleDeleteDispatch
        | GatewayGuildRoleUpdateDispatch
        | GatewayGuildScheduledEventCreateDispatch
        | GatewayGuildScheduledEventDeleteDispatch
        | GatewayGuildScheduledEventUpdateDispatch
        | GatewayGuildScheduledEventUserAddDispatch
        | GatewayGuildScheduledEventUserRemoveDispatch
        | GatewayGuildSoundboardSoundCreateDispatch
        | GatewayGuildSoundboardSoundDeleteDispatch
        | GatewayGuildSoundboardSoundUpdateDispatch
        | GatewayGuildSoundboardSoundsUpdateDispatch
        | GatewayGuildStickersUpdateDispatch
        | GatewayIntegrationCreateDispatch
        | GatewayIntegrationDeleteDispatch
        | GatewayIntegrationUpdateDispatch
        | GatewayInteractionCreateDispatch
        | GatewayInviteCreateDispatch
        | GatewayInviteDeleteDispatch
        | GatewayMessageCreateDispatch
        | GatewayMessageDeleteBulkDispatch
        | GatewayMessageDeleteDispatch
        | GatewayMessagePollVoteAddDispatch
        | GatewayMessagePollVoteRemoveDispatch
        | GatewayMessageReactionAddDispatch
        | GatewayMessageReactionRemoveAllDispatch
        | GatewayMessageReactionRemoveDispatch
        | GatewayMessageReactionRemoveEmojiDispatch
        | GatewayMessageUpdateDispatch
        | GatewayPresenceUpdateDispatch
        | GatewayRateLimitedDispatchGatewayOpcodesRequestGuildMembers
        | GatewayReadyDispatch
        | GatewayResumedDispatch
        | GatewaySoundboardSoundsDispatch
        | GatewayStageInstanceCreateDispatch
        | GatewayStageInstanceDeleteDispatch
        | GatewayStageInstanceUpdateDispatch
        | GatewaySubscriptionCreateDispatch
        | GatewaySubscriptionDeleteDispatch
        | GatewaySubscriptionUpdateDispatch
        | GatewayThreadCreateDispatch
        | GatewayThreadDeleteDispatch
        | GatewayThreadListSyncDispatch
        | GatewayThreadMemberUpdateDispatch
        | GatewayThreadMembersUpdateDispatch
        | GatewayThreadUpdateDispatch
        | GatewayTypingStartDispatch
        | GatewayUserUpdateDispatch
        | GatewayVoiceChannelEffectSendDispatch
        | GatewayVoiceChannelStartTimeUpdateDispatch
        | GatewayVoiceChannelStatusUpdateDispatch
        | GatewayVoiceServerUpdateDispatch
        | GatewayVoiceStateUpdateDispatch
        | GatewayWebhooksUpdateDispatch
    ]
):
    root: Annotated[
        GatewayApplicationCommandPermissionsUpdateDispatch
        | GatewayAutoModerationActionExecutionDispatch
        | GatewayAutoModerationRuleCreateDispatch
        | GatewayAutoModerationRuleDeleteDispatch
        | GatewayAutoModerationRuleUpdateDispatch
        | GatewayChannelCreateDispatch
        | GatewayChannelDeleteDispatch
        | GatewayChannelInfoDispatch
        | GatewayChannelPinsUpdateDispatch
        | GatewayChannelUpdateDispatch
        | GatewayEntitlementCreateDispatch
        | GatewayEntitlementDeleteDispatch
        | GatewayEntitlementUpdateDispatch
        | GatewayGuildAuditLogEntryCreateDispatch
        | GatewayGuildBanAddDispatch
        | GatewayGuildBanRemoveDispatch
        | GatewayGuildCreateDispatch
        | GatewayGuildDeleteDispatch
        | GatewayGuildEmojisUpdateDispatch
        | GatewayGuildIntegrationsUpdateDispatch
        | GatewayGuildMemberAddDispatch
        | GatewayGuildMemberRemoveDispatch
        | GatewayGuildMemberUpdateDispatch
        | GatewayGuildMembersChunkDispatch
        | GatewayGuildModifyDispatch
        | GatewayGuildRoleCreateDispatch
        | GatewayGuildRoleDeleteDispatch
        | GatewayGuildRoleUpdateDispatch
        | GatewayGuildScheduledEventCreateDispatch
        | GatewayGuildScheduledEventDeleteDispatch
        | GatewayGuildScheduledEventUpdateDispatch
        | GatewayGuildScheduledEventUserAddDispatch
        | GatewayGuildScheduledEventUserRemoveDispatch
        | GatewayGuildSoundboardSoundCreateDispatch
        | GatewayGuildSoundboardSoundDeleteDispatch
        | GatewayGuildSoundboardSoundUpdateDispatch
        | GatewayGuildSoundboardSoundsUpdateDispatch
        | GatewayGuildStickersUpdateDispatch
        | GatewayIntegrationCreateDispatch
        | GatewayIntegrationDeleteDispatch
        | GatewayIntegrationUpdateDispatch
        | GatewayInteractionCreateDispatch
        | GatewayInviteCreateDispatch
        | GatewayInviteDeleteDispatch
        | GatewayMessageCreateDispatch
        | GatewayMessageDeleteBulkDispatch
        | GatewayMessageDeleteDispatch
        | GatewayMessagePollVoteAddDispatch
        | GatewayMessagePollVoteRemoveDispatch
        | GatewayMessageReactionAddDispatch
        | GatewayMessageReactionRemoveAllDispatch
        | GatewayMessageReactionRemoveDispatch
        | GatewayMessageReactionRemoveEmojiDispatch
        | GatewayMessageUpdateDispatch
        | GatewayPresenceUpdateDispatch
        | GatewayRateLimitedDispatchGatewayOpcodesRequestGuildMembers
        | GatewayReadyDispatch
        | GatewayResumedDispatch
        | GatewaySoundboardSoundsDispatch
        | GatewayStageInstanceCreateDispatch
        | GatewayStageInstanceDeleteDispatch
        | GatewayStageInstanceUpdateDispatch
        | GatewaySubscriptionCreateDispatch
        | GatewaySubscriptionDeleteDispatch
        | GatewaySubscriptionUpdateDispatch
        | GatewayThreadCreateDispatch
        | GatewayThreadDeleteDispatch
        | GatewayThreadListSyncDispatch
        | GatewayThreadMemberUpdateDispatch
        | GatewayThreadMembersUpdateDispatch
        | GatewayThreadUpdateDispatch
        | GatewayTypingStartDispatch
        | GatewayUserUpdateDispatch
        | GatewayVoiceChannelEffectSendDispatch
        | GatewayVoiceChannelStartTimeUpdateDispatch
        | GatewayVoiceChannelStatusUpdateDispatch
        | GatewayVoiceServerUpdateDispatch
        | GatewayVoiceStateUpdateDispatch
        | GatewayWebhooksUpdateDispatch,
        Field(discriminator='t'),
    ]
