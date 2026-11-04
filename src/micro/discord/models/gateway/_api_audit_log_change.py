# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._api_audit_log_change_key_x24_remove_xb0993_ec89_d47316_d import APIAuditLogChangeKeyX24RemoveXB0993EC89D47316D
from ._api_audit_log_change_key_afk_channel_id import APIAuditLogChangeKeyAFKChannelId
from ._api_audit_log_change_key_afk_timeout import APIAuditLogChangeKeyAFKTimeout
from ._api_audit_log_change_key_allow import APIAuditLogChangeKeyAllow
from ._api_audit_log_change_key_application_id import APIAuditLogChangeKeyApplicationId
from ._api_audit_log_change_key_archived import APIAuditLogChangeKeyArchived
from ._api_audit_log_change_key_asset import APIAuditLogChangeKeyAsset
from ._api_audit_log_change_key_auto_archive_duration import APIAuditLogChangeKeyAutoArchiveDuration
from ._api_audit_log_change_key_available import APIAuditLogChangeKeyAvailable
from ._api_audit_log_change_key_available_tags import APIAuditLogChangeKeyAvailableTags
from ._api_audit_log_change_key_avatar_hash import APIAuditLogChangeKeyAvatarHash
from ._api_audit_log_change_key_banner_hash import APIAuditLogChangeKeyBannerHash
from ._api_audit_log_change_key_bitrate import APIAuditLogChangeKeyBitrate
from ._api_audit_log_change_key_channel_id import APIAuditLogChangeKeyChannelId
from ._api_audit_log_change_key_code import APIAuditLogChangeKeyCode
from ._api_audit_log_change_key_color import APIAuditLogChangeKeyColor
from ._api_audit_log_change_key_communication_disabled_until import APIAuditLogChangeKeyCommunicationDisabledUntil
from ._api_audit_log_change_key_deaf import APIAuditLogChangeKeyDeaf
from ._api_audit_log_change_key_default_auto_archive_duration import APIAuditLogChangeKeyDefaultAutoArchiveDuration
from ._api_audit_log_change_key_default_message_notifications import APIAuditLogChangeKeyDefaultMessageNotifications
from ._api_audit_log_change_key_default_reaction_emoji import APIAuditLogChangeKeyDefaultReactionEmoji
from ._api_audit_log_change_key_default_thread_rate_limit_per_user import APIAuditLogChangeKeyDefaultThreadRateLimitPerUser
from ._api_audit_log_change_key_deny import APIAuditLogChangeKeyDeny
from ._api_audit_log_change_key_description import APIAuditLogChangeKeyDescription
from ._api_audit_log_change_key_discovery_splash_hash import APIAuditLogChangeKeyDiscoverySplashHash
from ._api_audit_log_change_key_emoji_id import APIAuditLogChangeKeyEmojiId
from ._api_audit_log_change_key_emoji_name import APIAuditLogChangeKeyEmojiName
from ._api_audit_log_change_key_enable_emoticons import APIAuditLogChangeKeyEnableEmoticons
from ._api_audit_log_change_key_enabled import APIAuditLogChangeKeyEnabled
from ._api_audit_log_change_key_entity_type import APIAuditLogChangeKeyEntityType
from ._api_audit_log_change_key_event_type import APIAuditLogChangeKeyEventType
from ._api_audit_log_change_key_exempt_channels import APIAuditLogChangeKeyExemptChannels
from ._api_audit_log_change_key_exempt_roles import APIAuditLogChangeKeyExemptRoles
from ._api_audit_log_change_key_expire_behavior import APIAuditLogChangeKeyExpireBehavior
from ._api_audit_log_change_key_expire_grace_period import APIAuditLogChangeKeyExpireGracePeriod
from ._api_audit_log_change_key_explicit_content_filter import APIAuditLogChangeKeyExplicitContentFilter
from ._api_audit_log_change_key_flags import APIAuditLogChangeKeyFlags
from ._api_audit_log_change_key_format_type import APIAuditLogChangeKeyFormatType
from ._api_audit_log_change_key_guild_id import APIAuditLogChangeKeyGuildId
from ._api_audit_log_change_key_hoist import APIAuditLogChangeKeyHoist
from ._api_audit_log_change_key_icon_hash import APIAuditLogChangeKeyIconHash
from ._api_audit_log_change_key_id import APIAuditLogChangeKeyId
from ._api_audit_log_change_key_image_hash import APIAuditLogChangeKeyImageHash
from ._api_audit_log_change_key_inviter_id import APIAuditLogChangeKeyInviterId
from ._api_audit_log_change_key_location import APIAuditLogChangeKeyLocation
from ._api_audit_log_change_key_locked import APIAuditLogChangeKeyLocked
from ._api_audit_log_change_key_mfa_level import APIAuditLogChangeKeyMFALevel
from ._api_audit_log_change_key_max_age import APIAuditLogChangeKeyMaxAge
from ._api_audit_log_change_key_max_uses import APIAuditLogChangeKeyMaxUses
from ._api_audit_log_change_key_mentionable import APIAuditLogChangeKeyMentionable
from ._api_audit_log_change_key_mute import APIAuditLogChangeKeyMute
from ._api_audit_log_change_key_nsfw import APIAuditLogChangeKeyNSFW
from ._api_audit_log_change_key_name import APIAuditLogChangeKeyName
from ._api_audit_log_change_key_nick import APIAuditLogChangeKeyNick
from ._api_audit_log_change_key_owner_id import APIAuditLogChangeKeyOwnerId
from ._api_audit_log_change_key_permission_overwrites import APIAuditLogChangeKeyPermissionOverwrites
from ._api_audit_log_change_key_permissions import APIAuditLogChangeKeyPermissions
from ._api_audit_log_change_key_position import APIAuditLogChangeKeyPosition
from ._api_audit_log_change_key_preferred_locale import APIAuditLogChangeKeyPreferredLocale
from ._api_audit_log_change_key_premium_progress_bar_enabled import APIAuditLogChangeKeyPremiumProgressBarEnabled
from ._api_audit_log_change_key_privacy_level import APIAuditLogChangeKeyPrivacyLevel
from ._api_audit_log_change_key_prune_delete_days import APIAuditLogChangeKeyPruneDeleteDays
from ._api_audit_log_change_key_public_updates_channel_id import APIAuditLogChangeKeyPublicUpdatesChannelId
from ._api_audit_log_change_key_rtc_region import APIAuditLogChangeKeyRTCRegion
from ._api_audit_log_change_key_rate_limit_per_user import APIAuditLogChangeKeyRateLimitPerUser
from ._api_audit_log_change_key_region import APIAuditLogChangeKeyRegion
from ._api_audit_log_change_key_rules_channel_id import APIAuditLogChangeKeyRulesChannelId
from ._api_audit_log_change_key_safety_alerts_channel_id import APIAuditLogChangeKeySafetyAlertsChannelId
from ._api_audit_log_change_key_sound_id import APIAuditLogChangeKeySoundId
from ._api_audit_log_change_key_splash_hash import APIAuditLogChangeKeySplashHash
from ._api_audit_log_change_key_status import APIAuditLogChangeKeyStatus
from ._api_audit_log_change_key_system_channel_flags import APIAuditLogChangeKeySystemChannelFlags
from ._api_audit_log_change_key_system_channel_id import APIAuditLogChangeKeySystemChannelId
from ._api_audit_log_change_key_tags import APIAuditLogChangeKeyTags
from ._api_audit_log_change_key_temporary import APIAuditLogChangeKeyTemporary
from ._api_audit_log_change_key_topic import APIAuditLogChangeKeyTopic
from ._api_audit_log_change_key_trigger_metadata import APIAuditLogChangeKeyTriggerMetadata
from ._api_audit_log_change_key_trigger_type import APIAuditLogChangeKeyTriggerType
from ._api_audit_log_change_key_type import APIAuditLogChangeKeyType
from ._api_audit_log_change_key_user_id import APIAuditLogChangeKeyUserId
from ._api_audit_log_change_key_user_limit import APIAuditLogChangeKeyUserLimit
from ._api_audit_log_change_key_uses import APIAuditLogChangeKeyUses
from ._api_audit_log_change_key_vanity_url_code import APIAuditLogChangeKeyVanityURLCode
from ._api_audit_log_change_key_verification_level import APIAuditLogChangeKeyVerificationLevel
from ._api_audit_log_change_key_video_quality_mode import APIAuditLogChangeKeyVideoQualityMode
from ._api_audit_log_change_key_volume import APIAuditLogChangeKeyVolume
from ._api_audit_log_change_key_widget_channel_id import APIAuditLogChangeKeyWidgetChannelId
from ._api_audit_log_change_key_widget_enabled import APIAuditLogChangeKeyWidgetEnabled
from ._api_audit_log_change_key_x24_add_x82_e963_ba7969_e0_e4 import APIAuditLogChangeKeyX24AddX82E963BA7969E0E4
from ._api_audit_log_change_key_actions import APIAuditLogChangeKeyActions
from ._api_audit_log_change_key_recurrence_rule import APIAuditLogChangeKeyRecurrenceRule


class APIAuditLogChange(
    RootModel[
        APIAuditLogChangeKeyX24AddX82E963BA7969E0E4
        | APIAuditLogChangeKeyX24RemoveXB0993EC89D47316D
        | APIAuditLogChangeKeyAFKChannelId
        | APIAuditLogChangeKeyAFKTimeout
        | APIAuditLogChangeKeyActions
        | APIAuditLogChangeKeyAllow
        | APIAuditLogChangeKeyApplicationId
        | APIAuditLogChangeKeyArchived
        | APIAuditLogChangeKeyAsset
        | APIAuditLogChangeKeyAutoArchiveDuration
        | APIAuditLogChangeKeyAvailable
        | APIAuditLogChangeKeyAvailableTags
        | APIAuditLogChangeKeyAvatarHash
        | APIAuditLogChangeKeyBannerHash
        | APIAuditLogChangeKeyBitrate
        | APIAuditLogChangeKeyChannelId
        | APIAuditLogChangeKeyCode
        | APIAuditLogChangeKeyColor
        | APIAuditLogChangeKeyCommunicationDisabledUntil
        | APIAuditLogChangeKeyDeaf
        | APIAuditLogChangeKeyDefaultAutoArchiveDuration
        | APIAuditLogChangeKeyDefaultMessageNotifications
        | APIAuditLogChangeKeyDefaultReactionEmoji
        | APIAuditLogChangeKeyDefaultThreadRateLimitPerUser
        | APIAuditLogChangeKeyDeny
        | APIAuditLogChangeKeyDescription
        | APIAuditLogChangeKeyDiscoverySplashHash
        | APIAuditLogChangeKeyEmojiId
        | APIAuditLogChangeKeyEmojiName
        | APIAuditLogChangeKeyEnableEmoticons
        | APIAuditLogChangeKeyEnabled
        | APIAuditLogChangeKeyEntityType
        | APIAuditLogChangeKeyEventType
        | APIAuditLogChangeKeyExemptChannels
        | APIAuditLogChangeKeyExemptRoles
        | APIAuditLogChangeKeyExpireBehavior
        | APIAuditLogChangeKeyExpireGracePeriod
        | APIAuditLogChangeKeyExplicitContentFilter
        | APIAuditLogChangeKeyFlags
        | APIAuditLogChangeKeyFormatType
        | APIAuditLogChangeKeyGuildId
        | APIAuditLogChangeKeyHoist
        | APIAuditLogChangeKeyIconHash
        | APIAuditLogChangeKeyId
        | APIAuditLogChangeKeyImageHash
        | APIAuditLogChangeKeyInviterId
        | APIAuditLogChangeKeyLocation
        | APIAuditLogChangeKeyLocked
        | APIAuditLogChangeKeyMFALevel
        | APIAuditLogChangeKeyMaxAge
        | APIAuditLogChangeKeyMaxUses
        | APIAuditLogChangeKeyMentionable
        | APIAuditLogChangeKeyMute
        | APIAuditLogChangeKeyNSFW
        | APIAuditLogChangeKeyName
        | APIAuditLogChangeKeyNick
        | APIAuditLogChangeKeyOwnerId
        | APIAuditLogChangeKeyPermissionOverwrites
        | APIAuditLogChangeKeyPermissions
        | APIAuditLogChangeKeyPosition
        | APIAuditLogChangeKeyPreferredLocale
        | APIAuditLogChangeKeyPremiumProgressBarEnabled
        | APIAuditLogChangeKeyPrivacyLevel
        | APIAuditLogChangeKeyPruneDeleteDays
        | APIAuditLogChangeKeyPublicUpdatesChannelId
        | APIAuditLogChangeKeyRTCRegion
        | APIAuditLogChangeKeyRateLimitPerUser
        | APIAuditLogChangeKeyRecurrenceRule
        | APIAuditLogChangeKeyRegion
        | APIAuditLogChangeKeyRulesChannelId
        | APIAuditLogChangeKeySafetyAlertsChannelId
        | APIAuditLogChangeKeySoundId
        | APIAuditLogChangeKeySplashHash
        | APIAuditLogChangeKeyStatus
        | APIAuditLogChangeKeySystemChannelFlags
        | APIAuditLogChangeKeySystemChannelId
        | APIAuditLogChangeKeyTags
        | APIAuditLogChangeKeyTemporary
        | APIAuditLogChangeKeyTopic
        | APIAuditLogChangeKeyTriggerMetadata
        | APIAuditLogChangeKeyTriggerType
        | APIAuditLogChangeKeyType
        | APIAuditLogChangeKeyUserId
        | APIAuditLogChangeKeyUserLimit
        | APIAuditLogChangeKeyUses
        | APIAuditLogChangeKeyVanityURLCode
        | APIAuditLogChangeKeyVerificationLevel
        | APIAuditLogChangeKeyVideoQualityMode
        | APIAuditLogChangeKeyVolume
        | APIAuditLogChangeKeyWidgetChannelId
        | APIAuditLogChangeKeyWidgetEnabled
    ]
):
    root: Annotated[
        APIAuditLogChangeKeyX24AddX82E963BA7969E0E4
        | APIAuditLogChangeKeyX24RemoveXB0993EC89D47316D
        | APIAuditLogChangeKeyAFKChannelId
        | APIAuditLogChangeKeyAFKTimeout
        | APIAuditLogChangeKeyActions
        | APIAuditLogChangeKeyAllow
        | APIAuditLogChangeKeyApplicationId
        | APIAuditLogChangeKeyArchived
        | APIAuditLogChangeKeyAsset
        | APIAuditLogChangeKeyAutoArchiveDuration
        | APIAuditLogChangeKeyAvailable
        | APIAuditLogChangeKeyAvailableTags
        | APIAuditLogChangeKeyAvatarHash
        | APIAuditLogChangeKeyBannerHash
        | APIAuditLogChangeKeyBitrate
        | APIAuditLogChangeKeyChannelId
        | APIAuditLogChangeKeyCode
        | APIAuditLogChangeKeyColor
        | APIAuditLogChangeKeyCommunicationDisabledUntil
        | APIAuditLogChangeKeyDeaf
        | APIAuditLogChangeKeyDefaultAutoArchiveDuration
        | APIAuditLogChangeKeyDefaultMessageNotifications
        | APIAuditLogChangeKeyDefaultReactionEmoji
        | APIAuditLogChangeKeyDefaultThreadRateLimitPerUser
        | APIAuditLogChangeKeyDeny
        | APIAuditLogChangeKeyDescription
        | APIAuditLogChangeKeyDiscoverySplashHash
        | APIAuditLogChangeKeyEmojiId
        | APIAuditLogChangeKeyEmojiName
        | APIAuditLogChangeKeyEnableEmoticons
        | APIAuditLogChangeKeyEnabled
        | APIAuditLogChangeKeyEntityType
        | APIAuditLogChangeKeyEventType
        | APIAuditLogChangeKeyExemptChannels
        | APIAuditLogChangeKeyExemptRoles
        | APIAuditLogChangeKeyExpireBehavior
        | APIAuditLogChangeKeyExpireGracePeriod
        | APIAuditLogChangeKeyExplicitContentFilter
        | APIAuditLogChangeKeyFlags
        | APIAuditLogChangeKeyFormatType
        | APIAuditLogChangeKeyGuildId
        | APIAuditLogChangeKeyHoist
        | APIAuditLogChangeKeyIconHash
        | APIAuditLogChangeKeyId
        | APIAuditLogChangeKeyImageHash
        | APIAuditLogChangeKeyInviterId
        | APIAuditLogChangeKeyLocation
        | APIAuditLogChangeKeyLocked
        | APIAuditLogChangeKeyMFALevel
        | APIAuditLogChangeKeyMaxAge
        | APIAuditLogChangeKeyMaxUses
        | APIAuditLogChangeKeyMentionable
        | APIAuditLogChangeKeyMute
        | APIAuditLogChangeKeyNSFW
        | APIAuditLogChangeKeyName
        | APIAuditLogChangeKeyNick
        | APIAuditLogChangeKeyOwnerId
        | APIAuditLogChangeKeyPermissionOverwrites
        | APIAuditLogChangeKeyPermissions
        | APIAuditLogChangeKeyPosition
        | APIAuditLogChangeKeyPreferredLocale
        | APIAuditLogChangeKeyPremiumProgressBarEnabled
        | APIAuditLogChangeKeyPrivacyLevel
        | APIAuditLogChangeKeyPruneDeleteDays
        | APIAuditLogChangeKeyPublicUpdatesChannelId
        | APIAuditLogChangeKeyRTCRegion
        | APIAuditLogChangeKeyRateLimitPerUser
        | APIAuditLogChangeKeyRecurrenceRule
        | APIAuditLogChangeKeyRegion
        | APIAuditLogChangeKeyRulesChannelId
        | APIAuditLogChangeKeySafetyAlertsChannelId
        | APIAuditLogChangeKeySoundId
        | APIAuditLogChangeKeySplashHash
        | APIAuditLogChangeKeyStatus
        | APIAuditLogChangeKeySystemChannelFlags
        | APIAuditLogChangeKeySystemChannelId
        | APIAuditLogChangeKeyTags
        | APIAuditLogChangeKeyTemporary
        | APIAuditLogChangeKeyTopic
        | APIAuditLogChangeKeyTriggerMetadata
        | APIAuditLogChangeKeyTriggerType
        | APIAuditLogChangeKeyType
        | APIAuditLogChangeKeyUserId
        | APIAuditLogChangeKeyUserLimit
        | APIAuditLogChangeKeyUses
        | APIAuditLogChangeKeyVanityURLCode
        | APIAuditLogChangeKeyVerificationLevel
        | APIAuditLogChangeKeyVideoQualityMode
        | APIAuditLogChangeKeyVolume
        | APIAuditLogChangeKeyWidgetChannelId
        | APIAuditLogChangeKeyWidgetEnabled,
        Field(discriminator='key'),
    ]
