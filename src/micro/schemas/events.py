"""Generated Discord Gateway event schemas. Do not edit by hand."""

from micro.discord.models import gateway
from micro.service import DispatchSchema

APPLICATION_COMMAND_PERMISSIONS_UPDATE = DispatchSchema[
  gateway.GatewayApplicationCommandPermissionsUpdateDispatchData
](
  id='APPLICATION_COMMAND_PERMISSIONS_UPDATE',
  payload=gateway.GatewayApplicationCommandPermissionsUpdateDispatchData,
)

AUTO_MODERATION_ACTION_EXECUTION = DispatchSchema[
  gateway.GatewayAutoModerationActionExecutionDispatchData
](
  id='AUTO_MODERATION_ACTION_EXECUTION',
  payload=gateway.GatewayAutoModerationActionExecutionDispatchData,
)

AUTO_MODERATION_RULE_CREATE = DispatchSchema[gateway.APIAutoModerationRule](
  id='AUTO_MODERATION_RULE_CREATE',
  payload=gateway.APIAutoModerationRule,
)

AUTO_MODERATION_RULE_DELETE = DispatchSchema[gateway.APIAutoModerationRule](
  id='AUTO_MODERATION_RULE_DELETE',
  payload=gateway.APIAutoModerationRule,
)

AUTO_MODERATION_RULE_UPDATE = DispatchSchema[gateway.APIAutoModerationRule](
  id='AUTO_MODERATION_RULE_UPDATE',
  payload=gateway.APIAutoModerationRule,
)

CHANNEL_CREATE = DispatchSchema[gateway.GatewayChannelModifyDispatchData](
  id='CHANNEL_CREATE',
  payload=gateway.GatewayChannelModifyDispatchData,
)

CHANNEL_DELETE = DispatchSchema[gateway.GatewayChannelModifyDispatchData](
  id='CHANNEL_DELETE',
  payload=gateway.GatewayChannelModifyDispatchData,
)

CHANNEL_INFO = DispatchSchema[gateway.GatewayChannelInfoDispatchData](
  id='CHANNEL_INFO',
  payload=gateway.GatewayChannelInfoDispatchData,
)

CHANNEL_PINS_UPDATE = DispatchSchema[gateway.GatewayChannelPinsUpdateDispatchData](
  id='CHANNEL_PINS_UPDATE',
  payload=gateway.GatewayChannelPinsUpdateDispatchData,
)

CHANNEL_UPDATE = DispatchSchema[gateway.GatewayChannelModifyDispatchData](
  id='CHANNEL_UPDATE',
  payload=gateway.GatewayChannelModifyDispatchData,
)

ENTITLEMENT_CREATE = DispatchSchema[gateway.APIEntitlement](
  id='ENTITLEMENT_CREATE',
  payload=gateway.APIEntitlement,
)

ENTITLEMENT_DELETE = DispatchSchema[gateway.APIEntitlement](
  id='ENTITLEMENT_DELETE',
  payload=gateway.APIEntitlement,
)

ENTITLEMENT_UPDATE = DispatchSchema[gateway.APIEntitlement](
  id='ENTITLEMENT_UPDATE',
  payload=gateway.APIEntitlement,
)

GUILD_AUDIT_LOG_ENTRY_CREATE = DispatchSchema[
  gateway.GatewayGuildAuditLogEntryCreateDispatchData
](
  id='GUILD_AUDIT_LOG_ENTRY_CREATE',
  payload=gateway.GatewayGuildAuditLogEntryCreateDispatchData,
)

GUILD_BAN_ADD = DispatchSchema[gateway.GatewayGuildBanModifyDispatchData](
  id='GUILD_BAN_ADD',
  payload=gateway.GatewayGuildBanModifyDispatchData,
)

GUILD_BAN_REMOVE = DispatchSchema[gateway.GatewayGuildBanModifyDispatchData](
  id='GUILD_BAN_REMOVE',
  payload=gateway.GatewayGuildBanModifyDispatchData,
)

GUILD_CREATE = DispatchSchema[gateway.GatewayGuildCreateDispatchData](
  id='GUILD_CREATE',
  payload=gateway.GatewayGuildCreateDispatchData,
)

GUILD_DELETE = DispatchSchema[gateway.GatewayGuildDeleteDispatchData](
  id='GUILD_DELETE',
  payload=gateway.GatewayGuildDeleteDispatchData,
)

GUILD_EMOJIS_UPDATE = DispatchSchema[gateway.GatewayGuildEmojisUpdateDispatchData](
  id='GUILD_EMOJIS_UPDATE',
  payload=gateway.GatewayGuildEmojisUpdateDispatchData,
)

GUILD_INTEGRATIONS_UPDATE = DispatchSchema[
  gateway.GatewayGuildIntegrationsUpdateDispatchData
](
  id='GUILD_INTEGRATIONS_UPDATE',
  payload=gateway.GatewayGuildIntegrationsUpdateDispatchData,
)

GUILD_MEMBERS_CHUNK = DispatchSchema[gateway.GatewayGuildMembersChunkDispatchData](
  id='GUILD_MEMBERS_CHUNK',
  payload=gateway.GatewayGuildMembersChunkDispatchData,
)

GUILD_MEMBER_ADD = DispatchSchema[gateway.GatewayGuildMemberAddDispatchData](
  id='GUILD_MEMBER_ADD',
  payload=gateway.GatewayGuildMemberAddDispatchData,
)

GUILD_MEMBER_REMOVE = DispatchSchema[gateway.GatewayGuildMemberRemoveDispatchData](
  id='GUILD_MEMBER_REMOVE',
  payload=gateway.GatewayGuildMemberRemoveDispatchData,
)

GUILD_MEMBER_UPDATE = DispatchSchema[gateway.GatewayGuildMemberUpdateDispatchData](
  id='GUILD_MEMBER_UPDATE',
  payload=gateway.GatewayGuildMemberUpdateDispatchData,
)

GUILD_ROLE_CREATE = DispatchSchema[gateway.GatewayGuildRoleModifyDispatchData](
  id='GUILD_ROLE_CREATE',
  payload=gateway.GatewayGuildRoleModifyDispatchData,
)

GUILD_ROLE_DELETE = DispatchSchema[gateway.GatewayGuildRoleDeleteDispatchData](
  id='GUILD_ROLE_DELETE',
  payload=gateway.GatewayGuildRoleDeleteDispatchData,
)

GUILD_ROLE_UPDATE = DispatchSchema[gateway.GatewayGuildRoleModifyDispatchData](
  id='GUILD_ROLE_UPDATE',
  payload=gateway.GatewayGuildRoleModifyDispatchData,
)

GUILD_SCHEDULED_EVENT_CREATE = DispatchSchema[gateway.APIGuildScheduledEvent](
  id='GUILD_SCHEDULED_EVENT_CREATE',
  payload=gateway.APIGuildScheduledEvent,
)

GUILD_SCHEDULED_EVENT_DELETE = DispatchSchema[gateway.APIGuildScheduledEvent](
  id='GUILD_SCHEDULED_EVENT_DELETE',
  payload=gateway.APIGuildScheduledEvent,
)

GUILD_SCHEDULED_EVENT_UPDATE = DispatchSchema[gateway.APIGuildScheduledEvent](
  id='GUILD_SCHEDULED_EVENT_UPDATE',
  payload=gateway.APIGuildScheduledEvent,
)

GUILD_SCHEDULED_EVENT_USER_ADD = DispatchSchema[
  gateway.GatewayGuildScheduledEventUserAddDispatchData
](
  id='GUILD_SCHEDULED_EVENT_USER_ADD',
  payload=gateway.GatewayGuildScheduledEventUserAddDispatchData,
)

GUILD_SCHEDULED_EVENT_USER_REMOVE = DispatchSchema[
  gateway.GatewayGuildScheduledEventUserRemoveDispatchData
](
  id='GUILD_SCHEDULED_EVENT_USER_REMOVE',
  payload=gateway.GatewayGuildScheduledEventUserRemoveDispatchData,
)

GUILD_SOUNDBOARD_SOUNDS_UPDATE = DispatchSchema[
  gateway.GatewayGuildSoundboardSoundsUpdateDispatchData
](
  id='GUILD_SOUNDBOARD_SOUNDS_UPDATE',
  payload=gateway.GatewayGuildSoundboardSoundsUpdateDispatchData,
)

GUILD_SOUNDBOARD_SOUND_CREATE = DispatchSchema[gateway.APISoundboardSound](
  id='GUILD_SOUNDBOARD_SOUND_CREATE',
  payload=gateway.APISoundboardSound,
)

GUILD_SOUNDBOARD_SOUND_DELETE = DispatchSchema[
  gateway.GatewayGuildSoundboardSoundDeleteDispatchData
](
  id='GUILD_SOUNDBOARD_SOUND_DELETE',
  payload=gateway.GatewayGuildSoundboardSoundDeleteDispatchData,
)

GUILD_SOUNDBOARD_SOUND_UPDATE = DispatchSchema[gateway.APISoundboardSound](
  id='GUILD_SOUNDBOARD_SOUND_UPDATE',
  payload=gateway.APISoundboardSound,
)

GUILD_STICKERS_UPDATE = DispatchSchema[gateway.GatewayGuildStickersUpdateDispatchData](
  id='GUILD_STICKERS_UPDATE',
  payload=gateway.GatewayGuildStickersUpdateDispatchData,
)

GUILD_UPDATE = DispatchSchema[gateway.APIGuild](
  id='GUILD_UPDATE',
  payload=gateway.APIGuild,
)

INTEGRATION_CREATE = DispatchSchema[gateway.GatewayIntegrationCreateDispatchData](
  id='INTEGRATION_CREATE',
  payload=gateway.GatewayIntegrationCreateDispatchData,
)

INTEGRATION_DELETE = DispatchSchema[gateway.GatewayIntegrationDeleteDispatchData](
  id='INTEGRATION_DELETE',
  payload=gateway.GatewayIntegrationDeleteDispatchData,
)

INTEGRATION_UPDATE = DispatchSchema[gateway.GatewayIntegrationUpdateDispatchData](
  id='INTEGRATION_UPDATE',
  payload=gateway.GatewayIntegrationUpdateDispatchData,
)

INTERACTION_CREATE = DispatchSchema[gateway.APIInteraction](
  id='INTERACTION_CREATE',
  payload=gateway.APIInteraction,
)

INVITE_CREATE = DispatchSchema[gateway.GatewayInviteCreateDispatchData](
  id='INVITE_CREATE',
  payload=gateway.GatewayInviteCreateDispatchData,
)

INVITE_DELETE = DispatchSchema[gateway.GatewayInviteDeleteDispatchData](
  id='INVITE_DELETE',
  payload=gateway.GatewayInviteDeleteDispatchData,
)

MESSAGE_CREATE = DispatchSchema[gateway.GatewayMessageCreateDispatchData](
  id='MESSAGE_CREATE',
  payload=gateway.GatewayMessageCreateDispatchData,
)

MESSAGE_DELETE = DispatchSchema[gateway.GatewayMessageDeleteDispatchData](
  id='MESSAGE_DELETE',
  payload=gateway.GatewayMessageDeleteDispatchData,
)

MESSAGE_DELETE_BULK = DispatchSchema[gateway.GatewayMessageDeleteBulkDispatchData](
  id='MESSAGE_DELETE_BULK',
  payload=gateway.GatewayMessageDeleteBulkDispatchData,
)

MESSAGE_POLL_VOTE_ADD = DispatchSchema[gateway.GatewayMessagePollVoteDispatchData](
  id='MESSAGE_POLL_VOTE_ADD',
  payload=gateway.GatewayMessagePollVoteDispatchData,
)

MESSAGE_POLL_VOTE_REMOVE = DispatchSchema[gateway.GatewayMessagePollVoteDispatchData](
  id='MESSAGE_POLL_VOTE_REMOVE',
  payload=gateway.GatewayMessagePollVoteDispatchData,
)

MESSAGE_REACTION_ADD = DispatchSchema[gateway.GatewayMessageReactionAddDispatchData](
  id='MESSAGE_REACTION_ADD',
  payload=gateway.GatewayMessageReactionAddDispatchData,
)

MESSAGE_REACTION_REMOVE = DispatchSchema[gateway.GatewayMessageReactionRemoveDispatchData](
  id='MESSAGE_REACTION_REMOVE',
  payload=gateway.GatewayMessageReactionRemoveDispatchData,
)

MESSAGE_REACTION_REMOVE_ALL = DispatchSchema[gateway.GatewayMessageReactionRemoveData](
  id='MESSAGE_REACTION_REMOVE_ALL',
  payload=gateway.GatewayMessageReactionRemoveData,
)

MESSAGE_REACTION_REMOVE_EMOJI = DispatchSchema[
  gateway.GatewayMessageReactionRemoveEmojiDispatchData
](
  id='MESSAGE_REACTION_REMOVE_EMOJI',
  payload=gateway.GatewayMessageReactionRemoveEmojiDispatchData,
)

MESSAGE_UPDATE = DispatchSchema[gateway.GatewayMessageUpdateDispatchData](
  id='MESSAGE_UPDATE',
  payload=gateway.GatewayMessageUpdateDispatchData,
)

PRESENCE_UPDATE = DispatchSchema[gateway.GatewayPresenceUpdate](
  id='PRESENCE_UPDATE',
  payload=gateway.GatewayPresenceUpdate,
)

RATE_LIMITED = DispatchSchema[gateway.GatewayRateLimitedDispatchDataRequestGuildMembers](
  id='RATE_LIMITED',
  payload=gateway.GatewayRateLimitedDispatchDataRequestGuildMembers,
)

READY = DispatchSchema[gateway.GatewayReadyDispatchData](
  id='READY',
  payload=gateway.GatewayReadyDispatchData,
)

RESUMED = DispatchSchema[None](
  id='RESUMED',
  payload=None,
)

SOUNDBOARD_SOUNDS = DispatchSchema[gateway.GatewaySoundboardSoundsDispatchData](
  id='SOUNDBOARD_SOUNDS',
  payload=gateway.GatewaySoundboardSoundsDispatchData,
)

STAGE_INSTANCE_CREATE = DispatchSchema[gateway.APIStageInstance](
  id='STAGE_INSTANCE_CREATE',
  payload=gateway.APIStageInstance,
)

STAGE_INSTANCE_DELETE = DispatchSchema[gateway.APIStageInstance](
  id='STAGE_INSTANCE_DELETE',
  payload=gateway.APIStageInstance,
)

STAGE_INSTANCE_UPDATE = DispatchSchema[gateway.APIStageInstance](
  id='STAGE_INSTANCE_UPDATE',
  payload=gateway.APIStageInstance,
)

SUBSCRIPTION_CREATE = DispatchSchema[gateway.APISubscription](
  id='SUBSCRIPTION_CREATE',
  payload=gateway.APISubscription,
)

SUBSCRIPTION_DELETE = DispatchSchema[gateway.APISubscription](
  id='SUBSCRIPTION_DELETE',
  payload=gateway.APISubscription,
)

SUBSCRIPTION_UPDATE = DispatchSchema[gateway.APISubscription](
  id='SUBSCRIPTION_UPDATE',
  payload=gateway.APISubscription,
)

THREAD_CREATE = DispatchSchema[gateway.GatewayThreadCreateDispatchData](
  id='THREAD_CREATE',
  payload=gateway.GatewayThreadCreateDispatchData,
)

THREAD_DELETE = DispatchSchema[gateway.GatewayThreadDeleteDispatchData](
  id='THREAD_DELETE',
  payload=gateway.GatewayThreadDeleteDispatchData,
)

THREAD_LIST_SYNC = DispatchSchema[gateway.GatewayThreadListSync](
  id='THREAD_LIST_SYNC',
  payload=gateway.GatewayThreadListSync,
)

THREAD_MEMBERS_UPDATE = DispatchSchema[gateway.GatewayThreadMembersUpdate](
  id='THREAD_MEMBERS_UPDATE',
  payload=gateway.GatewayThreadMembersUpdate,
)

THREAD_MEMBER_UPDATE = DispatchSchema[gateway.GatewayThreadMemberUpdateDispatchData](
  id='THREAD_MEMBER_UPDATE',
  payload=gateway.GatewayThreadMemberUpdateDispatchData,
)

THREAD_UPDATE = DispatchSchema[gateway.GatewayThreadUpdateDispatchData](
  id='THREAD_UPDATE',
  payload=gateway.GatewayThreadUpdateDispatchData,
)

TYPING_START = DispatchSchema[gateway.GatewayTypingStartDispatchData](
  id='TYPING_START',
  payload=gateway.GatewayTypingStartDispatchData,
)

USER_UPDATE = DispatchSchema[gateway.APIUser](
  id='USER_UPDATE',
  payload=gateway.APIUser,
)

VOICE_CHANNEL_EFFECT_SEND = DispatchSchema[
  gateway.GatewayVoiceChannelEffectSendDispatchData
](
  id='VOICE_CHANNEL_EFFECT_SEND',
  payload=gateway.GatewayVoiceChannelEffectSendDispatchData,
)

VOICE_CHANNEL_START_TIME_UPDATE = DispatchSchema[
  gateway.GatewayVoiceChannelStartTimeUpdateDispatchData
](
  id='VOICE_CHANNEL_START_TIME_UPDATE',
  payload=gateway.GatewayVoiceChannelStartTimeUpdateDispatchData,
)

VOICE_CHANNEL_STATUS_UPDATE = DispatchSchema[
  gateway.GatewayVoiceChannelStatusUpdateDispatchData
](
  id='VOICE_CHANNEL_STATUS_UPDATE',
  payload=gateway.GatewayVoiceChannelStatusUpdateDispatchData,
)

VOICE_SERVER_UPDATE = DispatchSchema[gateway.GatewayVoiceServerUpdateDispatchData](
  id='VOICE_SERVER_UPDATE',
  payload=gateway.GatewayVoiceServerUpdateDispatchData,
)

VOICE_STATE_UPDATE = DispatchSchema[gateway.APIVoiceState](
  id='VOICE_STATE_UPDATE',
  payload=gateway.APIVoiceState,
)

WEBHOOKS_UPDATE = DispatchSchema[gateway.GatewayWebhooksUpdateDispatchData](
  id='WEBHOOKS_UPDATE',
  payload=gateway.GatewayWebhooksUpdateDispatchData,
)

__all__ = (
  'APPLICATION_COMMAND_PERMISSIONS_UPDATE',
  'AUTO_MODERATION_ACTION_EXECUTION',
  'AUTO_MODERATION_RULE_CREATE',
  'AUTO_MODERATION_RULE_DELETE',
  'AUTO_MODERATION_RULE_UPDATE',
  'CHANNEL_CREATE',
  'CHANNEL_DELETE',
  'CHANNEL_INFO',
  'CHANNEL_PINS_UPDATE',
  'CHANNEL_UPDATE',
  'ENTITLEMENT_CREATE',
  'ENTITLEMENT_DELETE',
  'ENTITLEMENT_UPDATE',
  'GUILD_AUDIT_LOG_ENTRY_CREATE',
  'GUILD_BAN_ADD',
  'GUILD_BAN_REMOVE',
  'GUILD_CREATE',
  'GUILD_DELETE',
  'GUILD_EMOJIS_UPDATE',
  'GUILD_INTEGRATIONS_UPDATE',
  'GUILD_MEMBERS_CHUNK',
  'GUILD_MEMBER_ADD',
  'GUILD_MEMBER_REMOVE',
  'GUILD_MEMBER_UPDATE',
  'GUILD_ROLE_CREATE',
  'GUILD_ROLE_DELETE',
  'GUILD_ROLE_UPDATE',
  'GUILD_SCHEDULED_EVENT_CREATE',
  'GUILD_SCHEDULED_EVENT_DELETE',
  'GUILD_SCHEDULED_EVENT_UPDATE',
  'GUILD_SCHEDULED_EVENT_USER_ADD',
  'GUILD_SCHEDULED_EVENT_USER_REMOVE',
  'GUILD_SOUNDBOARD_SOUNDS_UPDATE',
  'GUILD_SOUNDBOARD_SOUND_CREATE',
  'GUILD_SOUNDBOARD_SOUND_DELETE',
  'GUILD_SOUNDBOARD_SOUND_UPDATE',
  'GUILD_STICKERS_UPDATE',
  'GUILD_UPDATE',
  'INTEGRATION_CREATE',
  'INTEGRATION_DELETE',
  'INTEGRATION_UPDATE',
  'INTERACTION_CREATE',
  'INVITE_CREATE',
  'INVITE_DELETE',
  'MESSAGE_CREATE',
  'MESSAGE_DELETE',
  'MESSAGE_DELETE_BULK',
  'MESSAGE_POLL_VOTE_ADD',
  'MESSAGE_POLL_VOTE_REMOVE',
  'MESSAGE_REACTION_ADD',
  'MESSAGE_REACTION_REMOVE',
  'MESSAGE_REACTION_REMOVE_ALL',
  'MESSAGE_REACTION_REMOVE_EMOJI',
  'MESSAGE_UPDATE',
  'PRESENCE_UPDATE',
  'RATE_LIMITED',
  'READY',
  'RESUMED',
  'SOUNDBOARD_SOUNDS',
  'STAGE_INSTANCE_CREATE',
  'STAGE_INSTANCE_DELETE',
  'STAGE_INSTANCE_UPDATE',
  'SUBSCRIPTION_CREATE',
  'SUBSCRIPTION_DELETE',
  'SUBSCRIPTION_UPDATE',
  'THREAD_CREATE',
  'THREAD_DELETE',
  'THREAD_LIST_SYNC',
  'THREAD_MEMBERS_UPDATE',
  'THREAD_MEMBER_UPDATE',
  'THREAD_UPDATE',
  'TYPING_START',
  'USER_UPDATE',
  'VOICE_CHANNEL_EFFECT_SEND',
  'VOICE_CHANNEL_START_TIME_UPDATE',
  'VOICE_CHANNEL_STATUS_UPDATE',
  'VOICE_SERVER_UPDATE',
  'VOICE_STATE_UPDATE',
  'WEBHOOKS_UPDATE',
)
