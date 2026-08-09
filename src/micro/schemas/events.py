"""Generated Discord Gateway event schemas. Do not edit by hand."""

from micro.discord.models import gateway
from micro.service import EventSchema

APPLICATION_COMMAND_PERMISSIONS_UPDATE = EventSchema[
  gateway.GatewayApplicationCommandPermissionsUpdateDispatchData
](
  id='APPLICATION_COMMAND_PERMISSIONS_UPDATE',
  payload=gateway.GatewayApplicationCommandPermissionsUpdateDispatchData,
)

AUTO_MODERATION_ACTION_EXECUTION = EventSchema[
  gateway.GatewayAutoModerationActionExecutionDispatchData
](
  id='AUTO_MODERATION_ACTION_EXECUTION',
  payload=gateway.GatewayAutoModerationActionExecutionDispatchData,
)

AUTO_MODERATION_RULE_CREATE = EventSchema[gateway.APIAutoModerationRule](
  id='AUTO_MODERATION_RULE_CREATE',
  payload=gateway.APIAutoModerationRule,
)

AUTO_MODERATION_RULE_DELETE = EventSchema[gateway.APIAutoModerationRule](
  id='AUTO_MODERATION_RULE_DELETE',
  payload=gateway.APIAutoModerationRule,
)

AUTO_MODERATION_RULE_UPDATE = EventSchema[gateway.APIAutoModerationRule](
  id='AUTO_MODERATION_RULE_UPDATE',
  payload=gateway.APIAutoModerationRule,
)

CHANNEL_CREATE = EventSchema[gateway.GatewayChannelModifyDispatchData](
  id='CHANNEL_CREATE',
  payload=gateway.GatewayChannelModifyDispatchData,
)

CHANNEL_DELETE = EventSchema[gateway.GatewayChannelModifyDispatchData](
  id='CHANNEL_DELETE',
  payload=gateway.GatewayChannelModifyDispatchData,
)

CHANNEL_INFO = EventSchema[gateway.GatewayChannelInfoDispatchData](
  id='CHANNEL_INFO',
  payload=gateway.GatewayChannelInfoDispatchData,
)

CHANNEL_PINS_UPDATE = EventSchema[gateway.GatewayChannelPinsUpdateDispatchData](
  id='CHANNEL_PINS_UPDATE',
  payload=gateway.GatewayChannelPinsUpdateDispatchData,
)

CHANNEL_UPDATE = EventSchema[gateway.GatewayChannelModifyDispatchData](
  id='CHANNEL_UPDATE',
  payload=gateway.GatewayChannelModifyDispatchData,
)

ENTITLEMENT_CREATE = EventSchema[gateway.APIEntitlement](
  id='ENTITLEMENT_CREATE',
  payload=gateway.APIEntitlement,
)

ENTITLEMENT_DELETE = EventSchema[gateway.APIEntitlement](
  id='ENTITLEMENT_DELETE',
  payload=gateway.APIEntitlement,
)

ENTITLEMENT_UPDATE = EventSchema[gateway.APIEntitlement](
  id='ENTITLEMENT_UPDATE',
  payload=gateway.APIEntitlement,
)

GUILD_AUDIT_LOG_ENTRY_CREATE = EventSchema[
  gateway.GatewayGuildAuditLogEntryCreateDispatchData
](
  id='GUILD_AUDIT_LOG_ENTRY_CREATE',
  payload=gateway.GatewayGuildAuditLogEntryCreateDispatchData,
)

GUILD_BAN_ADD = EventSchema[gateway.GatewayGuildBanModifyDispatchData](
  id='GUILD_BAN_ADD',
  payload=gateway.GatewayGuildBanModifyDispatchData,
)

GUILD_BAN_REMOVE = EventSchema[gateway.GatewayGuildBanModifyDispatchData](
  id='GUILD_BAN_REMOVE',
  payload=gateway.GatewayGuildBanModifyDispatchData,
)

GUILD_CREATE = EventSchema[gateway.GatewayGuildCreateDispatchData](
  id='GUILD_CREATE',
  payload=gateway.GatewayGuildCreateDispatchData,
)

GUILD_DELETE = EventSchema[gateway.GatewayGuildDeleteDispatchData](
  id='GUILD_DELETE',
  payload=gateway.GatewayGuildDeleteDispatchData,
)

GUILD_EMOJIS_UPDATE = EventSchema[gateway.GatewayGuildEmojisUpdateDispatchData](
  id='GUILD_EMOJIS_UPDATE',
  payload=gateway.GatewayGuildEmojisUpdateDispatchData,
)

GUILD_INTEGRATIONS_UPDATE = EventSchema[
  gateway.GatewayGuildIntegrationsUpdateDispatchData
](
  id='GUILD_INTEGRATIONS_UPDATE',
  payload=gateway.GatewayGuildIntegrationsUpdateDispatchData,
)

GUILD_MEMBERS_CHUNK = EventSchema[gateway.GatewayGuildMembersChunkDispatchData](
  id='GUILD_MEMBERS_CHUNK',
  payload=gateway.GatewayGuildMembersChunkDispatchData,
)

GUILD_MEMBER_ADD = EventSchema[gateway.GatewayGuildMemberAddDispatchData](
  id='GUILD_MEMBER_ADD',
  payload=gateway.GatewayGuildMemberAddDispatchData,
)

GUILD_MEMBER_REMOVE = EventSchema[gateway.GatewayGuildMemberRemoveDispatchData](
  id='GUILD_MEMBER_REMOVE',
  payload=gateway.GatewayGuildMemberRemoveDispatchData,
)

GUILD_MEMBER_UPDATE = EventSchema[gateway.GatewayGuildMemberUpdateDispatchData](
  id='GUILD_MEMBER_UPDATE',
  payload=gateway.GatewayGuildMemberUpdateDispatchData,
)

GUILD_ROLE_CREATE = EventSchema[gateway.GatewayGuildRoleModifyDispatchData](
  id='GUILD_ROLE_CREATE',
  payload=gateway.GatewayGuildRoleModifyDispatchData,
)

GUILD_ROLE_DELETE = EventSchema[gateway.GatewayGuildRoleDeleteDispatchData](
  id='GUILD_ROLE_DELETE',
  payload=gateway.GatewayGuildRoleDeleteDispatchData,
)

GUILD_ROLE_UPDATE = EventSchema[gateway.GatewayGuildRoleModifyDispatchData](
  id='GUILD_ROLE_UPDATE',
  payload=gateway.GatewayGuildRoleModifyDispatchData,
)

GUILD_SCHEDULED_EVENT_CREATE = EventSchema[gateway.APIGuildScheduledEvent](
  id='GUILD_SCHEDULED_EVENT_CREATE',
  payload=gateway.APIGuildScheduledEvent,
)

GUILD_SCHEDULED_EVENT_DELETE = EventSchema[gateway.APIGuildScheduledEvent](
  id='GUILD_SCHEDULED_EVENT_DELETE',
  payload=gateway.APIGuildScheduledEvent,
)

GUILD_SCHEDULED_EVENT_UPDATE = EventSchema[gateway.APIGuildScheduledEvent](
  id='GUILD_SCHEDULED_EVENT_UPDATE',
  payload=gateway.APIGuildScheduledEvent,
)

GUILD_SCHEDULED_EVENT_USER_ADD = EventSchema[
  gateway.GatewayGuildScheduledEventUserAddDispatchData
](
  id='GUILD_SCHEDULED_EVENT_USER_ADD',
  payload=gateway.GatewayGuildScheduledEventUserAddDispatchData,
)

GUILD_SCHEDULED_EVENT_USER_REMOVE = EventSchema[
  gateway.GatewayGuildScheduledEventUserRemoveDispatchData
](
  id='GUILD_SCHEDULED_EVENT_USER_REMOVE',
  payload=gateway.GatewayGuildScheduledEventUserRemoveDispatchData,
)

GUILD_SOUNDBOARD_SOUNDS_UPDATE = EventSchema[
  gateway.GatewayGuildSoundboardSoundsUpdateDispatchData
](
  id='GUILD_SOUNDBOARD_SOUNDS_UPDATE',
  payload=gateway.GatewayGuildSoundboardSoundsUpdateDispatchData,
)

GUILD_SOUNDBOARD_SOUND_CREATE = EventSchema[gateway.APISoundboardSound](
  id='GUILD_SOUNDBOARD_SOUND_CREATE',
  payload=gateway.APISoundboardSound,
)

GUILD_SOUNDBOARD_SOUND_DELETE = EventSchema[
  gateway.GatewayGuildSoundboardSoundDeleteDispatchData
](
  id='GUILD_SOUNDBOARD_SOUND_DELETE',
  payload=gateway.GatewayGuildSoundboardSoundDeleteDispatchData,
)

GUILD_SOUNDBOARD_SOUND_UPDATE = EventSchema[gateway.APISoundboardSound](
  id='GUILD_SOUNDBOARD_SOUND_UPDATE',
  payload=gateway.APISoundboardSound,
)

GUILD_STICKERS_UPDATE = EventSchema[gateway.GatewayGuildStickersUpdateDispatchData](
  id='GUILD_STICKERS_UPDATE',
  payload=gateway.GatewayGuildStickersUpdateDispatchData,
)

GUILD_UPDATE = EventSchema[gateway.APIGuild](
  id='GUILD_UPDATE',
  payload=gateway.APIGuild,
)

INTEGRATION_CREATE = EventSchema[gateway.GatewayIntegrationCreateDispatchData](
  id='INTEGRATION_CREATE',
  payload=gateway.GatewayIntegrationCreateDispatchData,
)

INTEGRATION_DELETE = EventSchema[gateway.GatewayIntegrationDeleteDispatchData](
  id='INTEGRATION_DELETE',
  payload=gateway.GatewayIntegrationDeleteDispatchData,
)

INTEGRATION_UPDATE = EventSchema[gateway.GatewayIntegrationUpdateDispatchData](
  id='INTEGRATION_UPDATE',
  payload=gateway.GatewayIntegrationUpdateDispatchData,
)

INTERACTION_CREATE = EventSchema[gateway.APIInteraction](
  id='INTERACTION_CREATE',
  payload=gateway.APIInteraction,
)

INVITE_CREATE = EventSchema[gateway.GatewayInviteCreateDispatchData](
  id='INVITE_CREATE',
  payload=gateway.GatewayInviteCreateDispatchData,
)

INVITE_DELETE = EventSchema[gateway.GatewayInviteDeleteDispatchData](
  id='INVITE_DELETE',
  payload=gateway.GatewayInviteDeleteDispatchData,
)

MESSAGE_CREATE = EventSchema[gateway.GatewayMessageCreateDispatchData](
  id='MESSAGE_CREATE',
  payload=gateway.GatewayMessageCreateDispatchData,
)

MESSAGE_DELETE = EventSchema[gateway.GatewayMessageDeleteDispatchData](
  id='MESSAGE_DELETE',
  payload=gateway.GatewayMessageDeleteDispatchData,
)

MESSAGE_DELETE_BULK = EventSchema[gateway.GatewayMessageDeleteBulkDispatchData](
  id='MESSAGE_DELETE_BULK',
  payload=gateway.GatewayMessageDeleteBulkDispatchData,
)

MESSAGE_POLL_VOTE_ADD = EventSchema[gateway.GatewayMessagePollVoteDispatchData](
  id='MESSAGE_POLL_VOTE_ADD',
  payload=gateway.GatewayMessagePollVoteDispatchData,
)

MESSAGE_POLL_VOTE_REMOVE = EventSchema[gateway.GatewayMessagePollVoteDispatchData](
  id='MESSAGE_POLL_VOTE_REMOVE',
  payload=gateway.GatewayMessagePollVoteDispatchData,
)

MESSAGE_REACTION_ADD = EventSchema[gateway.GatewayMessageReactionAddDispatchData](
  id='MESSAGE_REACTION_ADD',
  payload=gateway.GatewayMessageReactionAddDispatchData,
)

MESSAGE_REACTION_REMOVE = EventSchema[gateway.GatewayMessageReactionRemoveDispatchData](
  id='MESSAGE_REACTION_REMOVE',
  payload=gateway.GatewayMessageReactionRemoveDispatchData,
)

MESSAGE_REACTION_REMOVE_ALL = EventSchema[gateway.GatewayMessageReactionRemoveData](
  id='MESSAGE_REACTION_REMOVE_ALL',
  payload=gateway.GatewayMessageReactionRemoveData,
)

MESSAGE_REACTION_REMOVE_EMOJI = EventSchema[
  gateway.GatewayMessageReactionRemoveEmojiDispatchData
](
  id='MESSAGE_REACTION_REMOVE_EMOJI',
  payload=gateway.GatewayMessageReactionRemoveEmojiDispatchData,
)

MESSAGE_UPDATE = EventSchema[gateway.GatewayMessageUpdateDispatchData](
  id='MESSAGE_UPDATE',
  payload=gateway.GatewayMessageUpdateDispatchData,
)

PRESENCE_UPDATE = EventSchema[gateway.GatewayPresenceUpdate](
  id='PRESENCE_UPDATE',
  payload=gateway.GatewayPresenceUpdate,
)

RATE_LIMITED = EventSchema[gateway.GatewayRateLimitedDispatchDataRequestGuildMembers](
  id='RATE_LIMITED',
  payload=gateway.GatewayRateLimitedDispatchDataRequestGuildMembers,
)

READY = EventSchema[gateway.GatewayReadyDispatchData](
  id='READY',
  payload=gateway.GatewayReadyDispatchData,
)

RESUMED = EventSchema[None](
  id='RESUMED',
  payload=None,
)

SOUNDBOARD_SOUNDS = EventSchema[gateway.GatewaySoundboardSoundsDispatchData](
  id='SOUNDBOARD_SOUNDS',
  payload=gateway.GatewaySoundboardSoundsDispatchData,
)

STAGE_INSTANCE_CREATE = EventSchema[gateway.APIStageInstance](
  id='STAGE_INSTANCE_CREATE',
  payload=gateway.APIStageInstance,
)

STAGE_INSTANCE_DELETE = EventSchema[gateway.APIStageInstance](
  id='STAGE_INSTANCE_DELETE',
  payload=gateway.APIStageInstance,
)

STAGE_INSTANCE_UPDATE = EventSchema[gateway.APIStageInstance](
  id='STAGE_INSTANCE_UPDATE',
  payload=gateway.APIStageInstance,
)

SUBSCRIPTION_CREATE = EventSchema[gateway.APISubscription](
  id='SUBSCRIPTION_CREATE',
  payload=gateway.APISubscription,
)

SUBSCRIPTION_DELETE = EventSchema[gateway.APISubscription](
  id='SUBSCRIPTION_DELETE',
  payload=gateway.APISubscription,
)

SUBSCRIPTION_UPDATE = EventSchema[gateway.APISubscription](
  id='SUBSCRIPTION_UPDATE',
  payload=gateway.APISubscription,
)

THREAD_CREATE = EventSchema[gateway.GatewayThreadCreateDispatchData](
  id='THREAD_CREATE',
  payload=gateway.GatewayThreadCreateDispatchData,
)

THREAD_DELETE = EventSchema[gateway.GatewayThreadDeleteDispatchData](
  id='THREAD_DELETE',
  payload=gateway.GatewayThreadDeleteDispatchData,
)

THREAD_LIST_SYNC = EventSchema[gateway.GatewayThreadListSync](
  id='THREAD_LIST_SYNC',
  payload=gateway.GatewayThreadListSync,
)

THREAD_MEMBERS_UPDATE = EventSchema[gateway.GatewayThreadMembersUpdate](
  id='THREAD_MEMBERS_UPDATE',
  payload=gateway.GatewayThreadMembersUpdate,
)

THREAD_MEMBER_UPDATE = EventSchema[gateway.GatewayThreadMemberUpdateDispatchData](
  id='THREAD_MEMBER_UPDATE',
  payload=gateway.GatewayThreadMemberUpdateDispatchData,
)

THREAD_UPDATE = EventSchema[gateway.GatewayThreadUpdateDispatchData](
  id='THREAD_UPDATE',
  payload=gateway.GatewayThreadUpdateDispatchData,
)

TYPING_START = EventSchema[gateway.GatewayTypingStartDispatchData](
  id='TYPING_START',
  payload=gateway.GatewayTypingStartDispatchData,
)

USER_UPDATE = EventSchema[gateway.APIUser](
  id='USER_UPDATE',
  payload=gateway.APIUser,
)

VOICE_CHANNEL_EFFECT_SEND = EventSchema[
  gateway.GatewayVoiceChannelEffectSendDispatchData
](
  id='VOICE_CHANNEL_EFFECT_SEND',
  payload=gateway.GatewayVoiceChannelEffectSendDispatchData,
)

VOICE_CHANNEL_START_TIME_UPDATE = EventSchema[
  gateway.GatewayVoiceChannelStartTimeUpdateDispatchData
](
  id='VOICE_CHANNEL_START_TIME_UPDATE',
  payload=gateway.GatewayVoiceChannelStartTimeUpdateDispatchData,
)

VOICE_CHANNEL_STATUS_UPDATE = EventSchema[
  gateway.GatewayVoiceChannelStatusUpdateDispatchData
](
  id='VOICE_CHANNEL_STATUS_UPDATE',
  payload=gateway.GatewayVoiceChannelStatusUpdateDispatchData,
)

VOICE_SERVER_UPDATE = EventSchema[gateway.GatewayVoiceServerUpdateDispatchData](
  id='VOICE_SERVER_UPDATE',
  payload=gateway.GatewayVoiceServerUpdateDispatchData,
)

VOICE_STATE_UPDATE = EventSchema[gateway.APIVoiceState](
  id='VOICE_STATE_UPDATE',
  payload=gateway.APIVoiceState,
)

WEBHOOKS_UPDATE = EventSchema[gateway.GatewayWebhooksUpdateDispatchData](
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
