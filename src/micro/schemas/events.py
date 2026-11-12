"""Generated Discord Gateway event schemas. Do not edit by hand.

Each schema, and the payload model it validates, is created on first use.
"""

from typing import TYPE_CHECKING, Any

from micro.service import DispatchSchema

if TYPE_CHECKING:
  from micro.discord import objects
  from micro.discord.models import gateway

  APPLICATION_COMMAND_PERMISSIONS_UPDATE: DispatchSchema[gateway.GatewayApplicationCommandPermissionsUpdateDispatchData]
  AUTO_MODERATION_ACTION_EXECUTION: DispatchSchema[gateway.GatewayAutoModerationActionExecutionDispatchData]
  AUTO_MODERATION_RULE_CREATE: DispatchSchema[gateway.APIAutoModerationRule]
  AUTO_MODERATION_RULE_DELETE: DispatchSchema[gateway.APIAutoModerationRule]
  AUTO_MODERATION_RULE_UPDATE: DispatchSchema[gateway.APIAutoModerationRule]
  CHANNEL_CREATE: DispatchSchema[objects.Channel]
  CHANNEL_DELETE: DispatchSchema[objects.Channel]
  CHANNEL_INFO: DispatchSchema[gateway.GatewayChannelInfoDispatchData]
  CHANNEL_PINS_UPDATE: DispatchSchema[gateway.GatewayChannelPinsUpdateDispatchData]
  CHANNEL_UPDATE: DispatchSchema[objects.Channel]
  ENTITLEMENT_CREATE: DispatchSchema[gateway.APIEntitlement]
  ENTITLEMENT_DELETE: DispatchSchema[gateway.APIEntitlement]
  ENTITLEMENT_UPDATE: DispatchSchema[gateway.APIEntitlement]
  GUILD_AUDIT_LOG_ENTRY_CREATE: DispatchSchema[gateway.GatewayGuildAuditLogEntryCreateDispatchData]
  GUILD_BAN_ADD: DispatchSchema[gateway.GatewayGuildBanModifyDispatchData]
  GUILD_BAN_REMOVE: DispatchSchema[gateway.GatewayGuildBanModifyDispatchData]
  GUILD_CREATE: DispatchSchema[objects.Guild]
  GUILD_DELETE: DispatchSchema[gateway.GatewayGuildDeleteDispatchData]
  GUILD_EMOJIS_UPDATE: DispatchSchema[gateway.GatewayGuildEmojisUpdateDispatchData]
  GUILD_INTEGRATIONS_UPDATE: DispatchSchema[gateway.GatewayGuildIntegrationsUpdateDispatchData]
  GUILD_MEMBERS_CHUNK: DispatchSchema[gateway.GatewayGuildMembersChunkDispatchData]
  GUILD_MEMBER_ADD: DispatchSchema[objects.Member]
  GUILD_MEMBER_REMOVE: DispatchSchema[gateway.GatewayGuildMemberRemoveDispatchData]
  GUILD_MEMBER_UPDATE: DispatchSchema[objects.Member]
  GUILD_ROLE_CREATE: DispatchSchema[gateway.GatewayGuildRoleModifyDispatchData]
  GUILD_ROLE_DELETE: DispatchSchema[gateway.GatewayGuildRoleDeleteDispatchData]
  GUILD_ROLE_UPDATE: DispatchSchema[gateway.GatewayGuildRoleModifyDispatchData]
  GUILD_SCHEDULED_EVENT_CREATE: DispatchSchema[gateway.APIGuildScheduledEvent]
  GUILD_SCHEDULED_EVENT_DELETE: DispatchSchema[gateway.APIGuildScheduledEvent]
  GUILD_SCHEDULED_EVENT_UPDATE: DispatchSchema[gateway.APIGuildScheduledEvent]
  GUILD_SCHEDULED_EVENT_USER_ADD: DispatchSchema[gateway.GatewayGuildScheduledEventUserAddDispatchData]
  GUILD_SCHEDULED_EVENT_USER_REMOVE: DispatchSchema[gateway.GatewayGuildScheduledEventUserRemoveDispatchData]
  GUILD_SOUNDBOARD_SOUNDS_UPDATE: DispatchSchema[gateway.GatewayGuildSoundboardSoundsUpdateDispatchData]
  GUILD_SOUNDBOARD_SOUND_CREATE: DispatchSchema[gateway.APISoundboardSound]
  GUILD_SOUNDBOARD_SOUND_DELETE: DispatchSchema[gateway.GatewayGuildSoundboardSoundDeleteDispatchData]
  GUILD_SOUNDBOARD_SOUND_UPDATE: DispatchSchema[gateway.APISoundboardSound]
  GUILD_STICKERS_UPDATE: DispatchSchema[gateway.GatewayGuildStickersUpdateDispatchData]
  GUILD_UPDATE: DispatchSchema[objects.Guild]
  INTEGRATION_CREATE: DispatchSchema[gateway.GatewayIntegrationCreateDispatchData]
  INTEGRATION_DELETE: DispatchSchema[gateway.GatewayIntegrationDeleteDispatchData]
  INTEGRATION_UPDATE: DispatchSchema[gateway.GatewayIntegrationUpdateDispatchData]
  INTERACTION_CREATE: DispatchSchema[gateway.APIInteraction]
  INVITE_CREATE: DispatchSchema[gateway.GatewayInviteCreateDispatchData]
  INVITE_DELETE: DispatchSchema[gateway.GatewayInviteDeleteDispatchData]
  MESSAGE_CREATE: DispatchSchema[objects.Message]
  MESSAGE_DELETE: DispatchSchema[gateway.GatewayMessageDeleteDispatchData]
  MESSAGE_DELETE_BULK: DispatchSchema[gateway.GatewayMessageDeleteBulkDispatchData]
  MESSAGE_POLL_VOTE_ADD: DispatchSchema[gateway.GatewayMessagePollVoteDispatchData]
  MESSAGE_POLL_VOTE_REMOVE: DispatchSchema[gateway.GatewayMessagePollVoteDispatchData]
  MESSAGE_REACTION_ADD: DispatchSchema[gateway.GatewayMessageReactionAddDispatchData]
  MESSAGE_REACTION_REMOVE: DispatchSchema[gateway.GatewayMessageReactionRemoveDispatchData]
  MESSAGE_REACTION_REMOVE_ALL: DispatchSchema[gateway.GatewayMessageReactionRemoveData]
  MESSAGE_REACTION_REMOVE_EMOJI: DispatchSchema[gateway.GatewayMessageReactionRemoveEmojiDispatchData]
  MESSAGE_UPDATE: DispatchSchema[objects.Message]
  PRESENCE_UPDATE: DispatchSchema[gateway.GatewayPresenceUpdate]
  RATE_LIMITED: DispatchSchema[gateway.GatewayRateLimitedDispatchDataRequestGuildMembers]
  READY: DispatchSchema[gateway.GatewayReadyDispatchData]
  RESUMED: DispatchSchema[None]
  SOUNDBOARD_SOUNDS: DispatchSchema[gateway.GatewaySoundboardSoundsDispatchData]
  STAGE_INSTANCE_CREATE: DispatchSchema[gateway.APIStageInstance]
  STAGE_INSTANCE_DELETE: DispatchSchema[gateway.APIStageInstance]
  STAGE_INSTANCE_UPDATE: DispatchSchema[gateway.APIStageInstance]
  SUBSCRIPTION_CREATE: DispatchSchema[gateway.APISubscription]
  SUBSCRIPTION_DELETE: DispatchSchema[gateway.APISubscription]
  SUBSCRIPTION_UPDATE: DispatchSchema[gateway.APISubscription]
  THREAD_CREATE: DispatchSchema[objects.Channel]
  THREAD_DELETE: DispatchSchema[gateway.GatewayThreadDeleteDispatchData]
  THREAD_LIST_SYNC: DispatchSchema[gateway.GatewayThreadListSync]
  THREAD_MEMBERS_UPDATE: DispatchSchema[gateway.GatewayThreadMembersUpdate]
  THREAD_MEMBER_UPDATE: DispatchSchema[gateway.GatewayThreadMemberUpdateDispatchData]
  THREAD_UPDATE: DispatchSchema[objects.Channel]
  TYPING_START: DispatchSchema[gateway.GatewayTypingStartDispatchData]
  USER_UPDATE: DispatchSchema[objects.User]
  VOICE_CHANNEL_EFFECT_SEND: DispatchSchema[gateway.GatewayVoiceChannelEffectSendDispatchData]
  VOICE_CHANNEL_START_TIME_UPDATE: DispatchSchema[gateway.GatewayVoiceChannelStartTimeUpdateDispatchData]
  VOICE_CHANNEL_STATUS_UPDATE: DispatchSchema[gateway.GatewayVoiceChannelStatusUpdateDispatchData]
  VOICE_SERVER_UPDATE: DispatchSchema[gateway.GatewayVoiceServerUpdateDispatchData]
  VOICE_STATE_UPDATE: DispatchSchema[gateway.APIVoiceState]
  WEBHOOKS_UPDATE: DispatchSchema[gateway.GatewayWebhooksUpdateDispatchData]

_PAYLOADS: dict[str, str | None] = {
  'APPLICATION_COMMAND_PERMISSIONS_UPDATE': 'GatewayApplicationCommandPermissionsUpdateDispatchData',
  'AUTO_MODERATION_ACTION_EXECUTION': 'GatewayAutoModerationActionExecutionDispatchData',
  'AUTO_MODERATION_RULE_CREATE': 'APIAutoModerationRule',
  'AUTO_MODERATION_RULE_DELETE': 'APIAutoModerationRule',
  'AUTO_MODERATION_RULE_UPDATE': 'APIAutoModerationRule',
  'CHANNEL_CREATE': 'Channel',
  'CHANNEL_DELETE': 'Channel',
  'CHANNEL_INFO': 'GatewayChannelInfoDispatchData',
  'CHANNEL_PINS_UPDATE': 'GatewayChannelPinsUpdateDispatchData',
  'CHANNEL_UPDATE': 'Channel',
  'ENTITLEMENT_CREATE': 'APIEntitlement',
  'ENTITLEMENT_DELETE': 'APIEntitlement',
  'ENTITLEMENT_UPDATE': 'APIEntitlement',
  'GUILD_AUDIT_LOG_ENTRY_CREATE': 'GatewayGuildAuditLogEntryCreateDispatchData',
  'GUILD_BAN_ADD': 'GatewayGuildBanModifyDispatchData',
  'GUILD_BAN_REMOVE': 'GatewayGuildBanModifyDispatchData',
  'GUILD_CREATE': 'Guild',
  'GUILD_DELETE': 'GatewayGuildDeleteDispatchData',
  'GUILD_EMOJIS_UPDATE': 'GatewayGuildEmojisUpdateDispatchData',
  'GUILD_INTEGRATIONS_UPDATE': 'GatewayGuildIntegrationsUpdateDispatchData',
  'GUILD_MEMBERS_CHUNK': 'GatewayGuildMembersChunkDispatchData',
  'GUILD_MEMBER_ADD': 'Member',
  'GUILD_MEMBER_REMOVE': 'GatewayGuildMemberRemoveDispatchData',
  'GUILD_MEMBER_UPDATE': 'Member',
  'GUILD_ROLE_CREATE': 'GatewayGuildRoleModifyDispatchData',
  'GUILD_ROLE_DELETE': 'GatewayGuildRoleDeleteDispatchData',
  'GUILD_ROLE_UPDATE': 'GatewayGuildRoleModifyDispatchData',
  'GUILD_SCHEDULED_EVENT_CREATE': 'APIGuildScheduledEvent',
  'GUILD_SCHEDULED_EVENT_DELETE': 'APIGuildScheduledEvent',
  'GUILD_SCHEDULED_EVENT_UPDATE': 'APIGuildScheduledEvent',
  'GUILD_SCHEDULED_EVENT_USER_ADD': 'GatewayGuildScheduledEventUserAddDispatchData',
  'GUILD_SCHEDULED_EVENT_USER_REMOVE': 'GatewayGuildScheduledEventUserRemoveDispatchData',
  'GUILD_SOUNDBOARD_SOUNDS_UPDATE': 'GatewayGuildSoundboardSoundsUpdateDispatchData',
  'GUILD_SOUNDBOARD_SOUND_CREATE': 'APISoundboardSound',
  'GUILD_SOUNDBOARD_SOUND_DELETE': 'GatewayGuildSoundboardSoundDeleteDispatchData',
  'GUILD_SOUNDBOARD_SOUND_UPDATE': 'APISoundboardSound',
  'GUILD_STICKERS_UPDATE': 'GatewayGuildStickersUpdateDispatchData',
  'GUILD_UPDATE': 'Guild',
  'INTEGRATION_CREATE': 'GatewayIntegrationCreateDispatchData',
  'INTEGRATION_DELETE': 'GatewayIntegrationDeleteDispatchData',
  'INTEGRATION_UPDATE': 'GatewayIntegrationUpdateDispatchData',
  'INTERACTION_CREATE': 'APIInteraction',
  'INVITE_CREATE': 'GatewayInviteCreateDispatchData',
  'INVITE_DELETE': 'GatewayInviteDeleteDispatchData',
  'MESSAGE_CREATE': 'Message',
  'MESSAGE_DELETE': 'GatewayMessageDeleteDispatchData',
  'MESSAGE_DELETE_BULK': 'GatewayMessageDeleteBulkDispatchData',
  'MESSAGE_POLL_VOTE_ADD': 'GatewayMessagePollVoteDispatchData',
  'MESSAGE_POLL_VOTE_REMOVE': 'GatewayMessagePollVoteDispatchData',
  'MESSAGE_REACTION_ADD': 'GatewayMessageReactionAddDispatchData',
  'MESSAGE_REACTION_REMOVE': 'GatewayMessageReactionRemoveDispatchData',
  'MESSAGE_REACTION_REMOVE_ALL': 'GatewayMessageReactionRemoveData',
  'MESSAGE_REACTION_REMOVE_EMOJI': 'GatewayMessageReactionRemoveEmojiDispatchData',
  'MESSAGE_UPDATE': 'Message',
  'PRESENCE_UPDATE': 'GatewayPresenceUpdate',
  'RATE_LIMITED': 'GatewayRateLimitedDispatchDataRequestGuildMembers',
  'READY': 'GatewayReadyDispatchData',
  'RESUMED': None,
  'SOUNDBOARD_SOUNDS': 'GatewaySoundboardSoundsDispatchData',
  'STAGE_INSTANCE_CREATE': 'APIStageInstance',
  'STAGE_INSTANCE_DELETE': 'APIStageInstance',
  'STAGE_INSTANCE_UPDATE': 'APIStageInstance',
  'SUBSCRIPTION_CREATE': 'APISubscription',
  'SUBSCRIPTION_DELETE': 'APISubscription',
  'SUBSCRIPTION_UPDATE': 'APISubscription',
  'THREAD_CREATE': 'Channel',
  'THREAD_DELETE': 'GatewayThreadDeleteDispatchData',
  'THREAD_LIST_SYNC': 'GatewayThreadListSync',
  'THREAD_MEMBERS_UPDATE': 'GatewayThreadMembersUpdate',
  'THREAD_MEMBER_UPDATE': 'GatewayThreadMemberUpdateDispatchData',
  'THREAD_UPDATE': 'Channel',
  'TYPING_START': 'GatewayTypingStartDispatchData',
  'USER_UPDATE': 'User',
  'VOICE_CHANNEL_EFFECT_SEND': 'GatewayVoiceChannelEffectSendDispatchData',
  'VOICE_CHANNEL_START_TIME_UPDATE': 'GatewayVoiceChannelStartTimeUpdateDispatchData',
  'VOICE_CHANNEL_STATUS_UPDATE': 'GatewayVoiceChannelStatusUpdateDispatchData',
  'VOICE_SERVER_UPDATE': 'GatewayVoiceServerUpdateDispatchData',
  'VOICE_STATE_UPDATE': 'APIVoiceState',
  'WEBHOOKS_UPDATE': 'GatewayWebhooksUpdateDispatchData',
}

_VIEWS = {
  'Channel',
  'Guild',
  'Member',
  'Message',
  'User',
}


def __getattr__(name: str) -> Any:
  try:
    payload = _PAYLOADS[name]
  except KeyError:
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
  from micro.discord import objects
  from micro.discord.models import gateway

  schema = DispatchSchema[Any](
    id=name,
    payload=None
    if payload is None
    else getattr(objects if payload in _VIEWS else gateway, payload),
  )
  globals()[name] = schema
  return schema


def __dir__() -> list[str]:
  return sorted(_PAYLOADS)


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
