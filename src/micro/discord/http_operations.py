# Generated from Discord's OpenAPI specification by scripts/generate_http_operations.py.
# Do not edit directly.

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from .models import http as models

type DiscordOperationId = Literal[
  "get_my_application",
  "update_my_application",
  "get_application",
  "update_application",
  "applications_get_activity_instance",
  "upload_application_attachment",
  "list_application_commands",
  "create_application_command",
  "bulk_set_application_commands",
  "delete_application_command",
  "get_application_command",
  "update_application_command",
  "list_application_emojis",
  "create_application_emoji",
  "delete_application_emoji",
  "get_application_emoji",
  "update_application_emoji",
  "get_entitlements",
  "create_entitlement",
  "delete_entitlement",
  "get_entitlement",
  "consume_entitlement",
  "list_guild_application_commands",
  "create_guild_application_command",
  "bulk_set_guild_application_commands",
  "list_guild_application_command_permissions",
  "delete_guild_application_command",
  "get_guild_application_command",
  "update_guild_application_command",
  "get_guild_application_command_permissions",
  "set_guild_application_command_permissions",
  "get_application_role_connections_metadata",
  "update_application_role_connections_metadata",
  "delete_channel",
  "get_channel",
  "update_channel",
  "follow_channel",
  "list_channel_invites",
  "create_channel_invite",
  "list_messages",
  "create_message",
  "bulk_delete_messages",
  "list_pins",
  "delete_pin",
  "create_pin",
  "delete_message",
  "get_message",
  "update_message",
  "crosspost_message",
  "delete_all_message_reactions",
  "delete_all_message_reactions_by_emoji",
  "list_message_reactions_by_emoji",
  "delete_my_message_reaction",
  "add_my_message_reaction",
  "delete_user_message_reaction",
  "create_thread_from_message",
  "delete_channel_permission_overwrite",
  "set_channel_permission_overwrite",
  "deprecated_list_pins",
  "deprecated_delete_pin",
  "deprecated_create_pin",
  "get_answer_voters",
  "poll_expire",
  "delete_group_dm_user",
  "add_group_dm_user",
  "send_soundboard_sound",
  "list_thread_members",
  "leave_thread",
  "join_thread",
  "delete_thread_member",
  "get_thread_member",
  "add_thread_member",
  "create_thread",
  "list_private_archived_threads",
  "list_public_archived_threads",
  "thread_search",
  "trigger_typing_indicator",
  "list_my_private_archived_threads",
  "update_voice_channel_status",
  "list_channel_webhooks",
  "create_webhook",
  "get_gateway",
  "get_bot_gateway",
  "get_guild_template",
  "get_guild",
  "update_guild",
  "list_guild_audit_log_entries",
  "list_auto_moderation_rules",
  "create_auto_moderation_rule",
  "delete_auto_moderation_rule",
  "get_auto_moderation_rule",
  "update_auto_moderation_rule",
  "list_guild_bans",
  "unban_user_from_guild",
  "get_guild_ban",
  "ban_user_from_guild",
  "bulk_ban_users_from_guild",
  "list_guild_channels",
  "bulk_update_guild_channels",
  "create_guild_channel",
  "list_guild_emojis",
  "create_guild_emoji",
  "delete_guild_emoji",
  "get_guild_emoji",
  "update_guild_emoji",
  "update_guild_incident_actions",
  "list_guild_integrations",
  "delete_guild_integration",
  "list_guild_invites",
  "list_guild_members",
  "update_my_guild_member",
  "search_guild_members",
  "delete_guild_member",
  "get_guild_member",
  "update_guild_member",
  "add_guild_member",
  "delete_guild_member_role",
  "add_guild_member_role",
  "guild_search",
  "get_guild_new_member_welcome",
  "get_guilds_onboarding",
  "put_guilds_onboarding",
  "get_guild_preview",
  "preview_prune_guild",
  "prune_guild",
  "list_guild_voice_regions",
  "get_guild_join_requests",
  "action_guild_join_request",
  "list_guild_roles",
  "bulk_update_guild_roles",
  "create_guild_role",
  "guild_role_member_counts",
  "delete_guild_role",
  "get_guild_role",
  "update_guild_role",
  "list_guild_scheduled_events",
  "create_guild_scheduled_event",
  "delete_guild_scheduled_event",
  "get_guild_scheduled_event",
  "update_guild_scheduled_event",
  "create_guild_scheduled_event_exception",
  "delete_guild_scheduled_event_exception",
  "update_guild_scheduled_event_exception",
  "list_guild_scheduled_event_users",
  "count_guild_scheduled_event_users",
  "list_guild_scheduled_event_exception_users",
  "list_guild_soundboard_sounds",
  "create_guild_soundboard_sound",
  "delete_guild_soundboard_sound",
  "get_guild_soundboard_sound",
  "update_guild_soundboard_sound",
  "list_guild_stickers",
  "create_guild_sticker",
  "delete_guild_sticker",
  "get_guild_sticker",
  "update_guild_sticker",
  "list_guild_templates",
  "create_guild_template",
  "delete_guild_template",
  "update_guild_template",
  "sync_guild_template",
  "get_active_guild_threads",
  "get_guild_vanity_url",
  "get_self_voice_state",
  "update_self_voice_state",
  "get_voice_state",
  "update_voice_state",
  "get_guild_webhooks",
  "get_guild_welcome_screen",
  "update_guild_welcome_screen",
  "get_guild_widget_settings",
  "update_guild_widget_settings",
  "get_guild_widget",
  "get_guild_widget_png",
  "create_interaction_response",
  "invite_revoke",
  "invite_resolve",
  "get_invite_target_users",
  "update_invite_target_users",
  "get_invite_target_users_job_status",
  "create_lobby",
  "create_or_join_lobby",
  "delete_lobby",
  "get_lobby",
  "edit_lobby",
  "edit_lobby_channel_link",
  "leave_lobby",
  "create_linked_lobby_guild_invite_for_self",
  "bulk_update_lobby_members",
  "delete_lobby_member",
  "add_lobby_member",
  "create_linked_lobby_guild_invite_for_user",
  "get_lobby_messages",
  "create_lobby_message",
  "update_lobby_message_external_moderation_metadata",
  "get_my_oauth2_authorization",
  "get_my_oauth2_application",
  "get_public_keys",
  "get_openid_connect_userinfo",
  "update_user_message_external_moderation_metadata",
  "partner_sdk_unmerge_provisional_account",
  "bot_partner_sdk_unmerge_provisional_account",
  "partner_sdk_token",
  "bot_partner_sdk_token",
  "get_sku_subscriptions",
  "get_sku_subscription",
  "get_soundboard_default_sounds",
  "create_stage_instance",
  "delete_stage_instance",
  "get_stage_instance",
  "update_stage_instance",
  "list_sticker_packs",
  "get_sticker_pack",
  "get_sticker",
  "get_my_user",
  "update_my_user",
  "get_current_user_application_entitlements",
  "delete_application_user_role_connection",
  "get_application_user_role_connection",
  "update_application_user_role_connection",
  "create_dm",
  "list_my_connections",
  "list_my_guilds",
  "leave_guild",
  "get_my_guild_member",
  "get_user",
  "list_voice_regions",
  "delete_webhook",
  "get_webhook",
  "update_webhook",
  "delete_webhook_by_token",
  "get_webhook_by_token",
  "update_webhook_by_token",
  "execute_webhook",
  "execute_github_compatible_webhook",
  "delete_original_webhook_message",
  "get_original_webhook_message",
  "update_original_webhook_message",
  "delete_webhook_message",
  "get_webhook_message",
  "update_webhook_message",
  "execute_slack_compatible_webhook",
]


@dataclass(frozen=True, slots=True)
class DiscordHTTPOperation:
  id: DiscordOperationId
  method: str
  path: str
  input_model: type[BaseModel]
  path_fields: tuple[str, ...]
  query_fields: tuple[str, ...]
  header_fields: tuple[str, ...]
  content_types: tuple[str, ...]
  success_statuses: tuple[int, ...]


HTTP_OPERATIONS: dict[DiscordOperationId, DiscordHTTPOperation] = {
  "get_my_application": DiscordHTTPOperation(
    id="get_my_application",
    method="GET",
    path="/applications/@me",
    input_model=models.DiscordHTTPGetMyApplicationInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_my_application": DiscordHTTPOperation(
    id="update_my_application",
    method="PATCH",
    path="/applications/@me",
    input_model=models.DiscordHTTPUpdateMyApplicationInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_application": DiscordHTTPOperation(
    id="get_application",
    method="GET",
    path="/applications/{application_id}",
    input_model=models.DiscordHTTPGetApplicationInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_application": DiscordHTTPOperation(
    id="update_application",
    method="PATCH",
    path="/applications/{application_id}",
    input_model=models.DiscordHTTPUpdateApplicationInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "applications_get_activity_instance": DiscordHTTPOperation(
    id="applications_get_activity_instance",
    method="GET",
    path="/applications/{application_id}/activity-instances/{instance_id}",
    input_model=models.DiscordHTTPApplicationsGetActivityInstanceInput,
    path_fields=('application_id', 'instance_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "upload_application_attachment": DiscordHTTPOperation(
    id="upload_application_attachment",
    method="POST",
    path="/applications/{application_id}/attachment",
    input_model=models.DiscordHTTPUploadApplicationAttachmentInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('multipart/form-data',),
    success_statuses=(200,),
  ),
  "list_application_commands": DiscordHTTPOperation(
    id="list_application_commands",
    method="GET",
    path="/applications/{application_id}/commands",
    input_model=models.DiscordHTTPListApplicationCommandsInput,
    path_fields=('application_id',),
    query_fields=('with_localizations',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_application_command": DiscordHTTPOperation(
    id="create_application_command",
    method="POST",
    path="/applications/{application_id}/commands",
    input_model=models.DiscordHTTPCreateApplicationCommandInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200, 201),
  ),
  "bulk_set_application_commands": DiscordHTTPOperation(
    id="bulk_set_application_commands",
    method="PUT",
    path="/applications/{application_id}/commands",
    input_model=models.DiscordHTTPBulkSetApplicationCommandsInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_application_command": DiscordHTTPOperation(
    id="delete_application_command",
    method="DELETE",
    path="/applications/{application_id}/commands/{command_id}",
    input_model=models.DiscordHTTPDeleteApplicationCommandInput,
    path_fields=('application_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_application_command": DiscordHTTPOperation(
    id="get_application_command",
    method="GET",
    path="/applications/{application_id}/commands/{command_id}",
    input_model=models.DiscordHTTPGetApplicationCommandInput,
    path_fields=('application_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_application_command": DiscordHTTPOperation(
    id="update_application_command",
    method="PATCH",
    path="/applications/{application_id}/commands/{command_id}",
    input_model=models.DiscordHTTPUpdateApplicationCommandInput,
    path_fields=('application_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_application_emojis": DiscordHTTPOperation(
    id="list_application_emojis",
    method="GET",
    path="/applications/{application_id}/emojis",
    input_model=models.DiscordHTTPListApplicationEmojisInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_application_emoji": DiscordHTTPOperation(
    id="create_application_emoji",
    method="POST",
    path="/applications/{application_id}/emojis",
    input_model=models.DiscordHTTPCreateApplicationEmojiInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201,),
  ),
  "delete_application_emoji": DiscordHTTPOperation(
    id="delete_application_emoji",
    method="DELETE",
    path="/applications/{application_id}/emojis/{emoji_id}",
    input_model=models.DiscordHTTPDeleteApplicationEmojiInput,
    path_fields=('application_id', 'emoji_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_application_emoji": DiscordHTTPOperation(
    id="get_application_emoji",
    method="GET",
    path="/applications/{application_id}/emojis/{emoji_id}",
    input_model=models.DiscordHTTPGetApplicationEmojiInput,
    path_fields=('application_id', 'emoji_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_application_emoji": DiscordHTTPOperation(
    id="update_application_emoji",
    method="PATCH",
    path="/applications/{application_id}/emojis/{emoji_id}",
    input_model=models.DiscordHTTPUpdateApplicationEmojiInput,
    path_fields=('application_id', 'emoji_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_entitlements": DiscordHTTPOperation(
    id="get_entitlements",
    method="GET",
    path="/applications/{application_id}/entitlements",
    input_model=models.DiscordHTTPGetEntitlementsInput,
    path_fields=('application_id',),
    query_fields=(
      'user_id',
      'sku_ids',
      'guild_id',
      'before',
      'after',
      'limit',
      'exclude_ended',
      'exclude_deleted',
      'only_active',
    ),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_entitlement": DiscordHTTPOperation(
    id="create_entitlement",
    method="POST",
    path="/applications/{application_id}/entitlements",
    input_model=models.DiscordHTTPCreateEntitlementInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_entitlement": DiscordHTTPOperation(
    id="delete_entitlement",
    method="DELETE",
    path="/applications/{application_id}/entitlements/{entitlement_id}",
    input_model=models.DiscordHTTPDeleteEntitlementInput,
    path_fields=('application_id', 'entitlement_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_entitlement": DiscordHTTPOperation(
    id="get_entitlement",
    method="GET",
    path="/applications/{application_id}/entitlements/{entitlement_id}",
    input_model=models.DiscordHTTPGetEntitlementInput,
    path_fields=('application_id', 'entitlement_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "consume_entitlement": DiscordHTTPOperation(
    id="consume_entitlement",
    method="POST",
    path="/applications/{application_id}/entitlements/{entitlement_id}/consume",
    input_model=models.DiscordHTTPConsumeEntitlementInput,
    path_fields=('application_id', 'entitlement_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "list_guild_application_commands": DiscordHTTPOperation(
    id="list_guild_application_commands",
    method="GET",
    path="/applications/{application_id}/guilds/{guild_id}/commands",
    input_model=models.DiscordHTTPListGuildApplicationCommandsInput,
    path_fields=('application_id', 'guild_id'),
    query_fields=('with_localizations',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_guild_application_command": DiscordHTTPOperation(
    id="create_guild_application_command",
    method="POST",
    path="/applications/{application_id}/guilds/{guild_id}/commands",
    input_model=models.DiscordHTTPCreateGuildApplicationCommandInput,
    path_fields=('application_id', 'guild_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200, 201),
  ),
  "bulk_set_guild_application_commands": DiscordHTTPOperation(
    id="bulk_set_guild_application_commands",
    method="PUT",
    path="/applications/{application_id}/guilds/{guild_id}/commands",
    input_model=models.DiscordHTTPBulkSetGuildApplicationCommandsInput,
    path_fields=('application_id', 'guild_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_application_command_permissions": DiscordHTTPOperation(
    id="list_guild_application_command_permissions",
    method="GET",
    path="/applications/{application_id}/guilds/{guild_id}/commands/permissions",
    input_model=models.DiscordHTTPListGuildApplicationCommandPermissionsInput,
    path_fields=('application_id', 'guild_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_guild_application_command": DiscordHTTPOperation(
    id="delete_guild_application_command",
    method="DELETE",
    path="/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
    input_model=models.DiscordHTTPDeleteGuildApplicationCommandInput,
    path_fields=('application_id', 'guild_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_guild_application_command": DiscordHTTPOperation(
    id="get_guild_application_command",
    method="GET",
    path="/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
    input_model=models.DiscordHTTPGetGuildApplicationCommandInput,
    path_fields=('application_id', 'guild_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_application_command": DiscordHTTPOperation(
    id="update_guild_application_command",
    method="PATCH",
    path="/applications/{application_id}/guilds/{guild_id}/commands/{command_id}",
    input_model=models.DiscordHTTPUpdateGuildApplicationCommandInput,
    path_fields=('application_id', 'guild_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_guild_application_command_permissions": DiscordHTTPOperation(
    id="get_guild_application_command_permissions",
    method="GET",
    path="/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions",
    input_model=models.DiscordHTTPGetGuildApplicationCommandPermissionsInput,
    path_fields=('application_id', 'guild_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "set_guild_application_command_permissions": DiscordHTTPOperation(
    id="set_guild_application_command_permissions",
    method="PUT",
    path="/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions",
    input_model=models.DiscordHTTPSetGuildApplicationCommandPermissionsInput,
    path_fields=('application_id', 'guild_id', 'command_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_application_role_connections_metadata": DiscordHTTPOperation(
    id="get_application_role_connections_metadata",
    method="GET",
    path="/applications/{application_id}/role-connections/metadata",
    input_model=models.DiscordHTTPGetApplicationRoleConnectionsMetadataInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_application_role_connections_metadata": DiscordHTTPOperation(
    id="update_application_role_connections_metadata",
    method="PUT",
    path="/applications/{application_id}/role-connections/metadata",
    input_model=models.DiscordHTTPUpdateApplicationRoleConnectionsMetadataInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_channel": DiscordHTTPOperation(
    id="delete_channel",
    method="DELETE",
    path="/channels/{channel_id}",
    input_model=models.DiscordHTTPDeleteChannelInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_channel": DiscordHTTPOperation(
    id="get_channel",
    method="GET",
    path="/channels/{channel_id}",
    input_model=models.DiscordHTTPGetChannelInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_channel": DiscordHTTPOperation(
    id="update_channel",
    method="PATCH",
    path="/channels/{channel_id}",
    input_model=models.DiscordHTTPUpdateChannelInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "follow_channel": DiscordHTTPOperation(
    id="follow_channel",
    method="POST",
    path="/channels/{channel_id}/followers",
    input_model=models.DiscordHTTPFollowChannelInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_channel_invites": DiscordHTTPOperation(
    id="list_channel_invites",
    method="GET",
    path="/channels/{channel_id}/invites",
    input_model=models.DiscordHTTPListChannelInvitesInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_channel_invite": DiscordHTTPOperation(
    id="create_channel_invite",
    method="POST",
    path="/channels/{channel_id}/invites",
    input_model=models.DiscordHTTPCreateChannelInviteInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200, 204),
  ),
  "list_messages": DiscordHTTPOperation(
    id="list_messages",
    method="GET",
    path="/channels/{channel_id}/messages",
    input_model=models.DiscordHTTPListMessagesInput,
    path_fields=('channel_id',),
    query_fields=('around', 'before', 'after', 'limit'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_message": DiscordHTTPOperation(
    id="create_message",
    method="POST",
    path="/channels/{channel_id}/messages",
    input_model=models.DiscordHTTPCreateMessageInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200,),
  ),
  "bulk_delete_messages": DiscordHTTPOperation(
    id="bulk_delete_messages",
    method="POST",
    path="/channels/{channel_id}/messages/bulk-delete",
    input_model=models.DiscordHTTPBulkDeleteMessagesInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "list_pins": DiscordHTTPOperation(
    id="list_pins",
    method="GET",
    path="/channels/{channel_id}/messages/pins",
    input_model=models.DiscordHTTPListPinsInput,
    path_fields=('channel_id',),
    query_fields=('before', 'limit'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_pin": DiscordHTTPOperation(
    id="delete_pin",
    method="DELETE",
    path="/channels/{channel_id}/messages/pins/{message_id}",
    input_model=models.DiscordHTTPDeletePinInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "create_pin": DiscordHTTPOperation(
    id="create_pin",
    method="PUT",
    path="/channels/{channel_id}/messages/pins/{message_id}",
    input_model=models.DiscordHTTPCreatePinInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "delete_message": DiscordHTTPOperation(
    id="delete_message",
    method="DELETE",
    path="/channels/{channel_id}/messages/{message_id}",
    input_model=models.DiscordHTTPDeleteMessageInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_message": DiscordHTTPOperation(
    id="get_message",
    method="GET",
    path="/channels/{channel_id}/messages/{message_id}",
    input_model=models.DiscordHTTPGetMessageInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_message": DiscordHTTPOperation(
    id="update_message",
    method="PATCH",
    path="/channels/{channel_id}/messages/{message_id}",
    input_model=models.DiscordHTTPUpdateMessageInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200,),
  ),
  "crosspost_message": DiscordHTTPOperation(
    id="crosspost_message",
    method="POST",
    path="/channels/{channel_id}/messages/{message_id}/crosspost",
    input_model=models.DiscordHTTPCrosspostMessageInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_all_message_reactions": DiscordHTTPOperation(
    id="delete_all_message_reactions",
    method="DELETE",
    path="/channels/{channel_id}/messages/{message_id}/reactions",
    input_model=models.DiscordHTTPDeleteAllMessageReactionsInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "delete_all_message_reactions_by_emoji": DiscordHTTPOperation(
    id="delete_all_message_reactions_by_emoji",
    method="DELETE",
    path="/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}",
    input_model=models.DiscordHTTPDeleteAllMessageReactionsByEmojiInput,
    path_fields=('channel_id', 'message_id', 'emoji_name'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "list_message_reactions_by_emoji": DiscordHTTPOperation(
    id="list_message_reactions_by_emoji",
    method="GET",
    path="/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}",
    input_model=models.DiscordHTTPListMessageReactionsByEmojiInput,
    path_fields=('channel_id', 'message_id', 'emoji_name'),
    query_fields=('after', 'limit', 'type'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_my_message_reaction": DiscordHTTPOperation(
    id="delete_my_message_reaction",
    method="DELETE",
    path="/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}/@me",
    input_model=models.DiscordHTTPDeleteMyMessageReactionInput,
    path_fields=('channel_id', 'message_id', 'emoji_name'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "add_my_message_reaction": DiscordHTTPOperation(
    id="add_my_message_reaction",
    method="PUT",
    path="/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}/@me",
    input_model=models.DiscordHTTPAddMyMessageReactionInput,
    path_fields=('channel_id', 'message_id', 'emoji_name'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "delete_user_message_reaction": DiscordHTTPOperation(
    id="delete_user_message_reaction",
    method="DELETE",
    path="/channels/{channel_id}/messages/{message_id}/reactions/{emoji_name}/{user_id}",
    input_model=models.DiscordHTTPDeleteUserMessageReactionInput,
    path_fields=('channel_id', 'message_id', 'emoji_name', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "create_thread_from_message": DiscordHTTPOperation(
    id="create_thread_from_message",
    method="POST",
    path="/channels/{channel_id}/messages/{message_id}/threads",
    input_model=models.DiscordHTTPCreateThreadFromMessageInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201,),
  ),
  "delete_channel_permission_overwrite": DiscordHTTPOperation(
    id="delete_channel_permission_overwrite",
    method="DELETE",
    path="/channels/{channel_id}/permissions/{overwrite_id}",
    input_model=models.DiscordHTTPDeleteChannelPermissionOverwriteInput,
    path_fields=('channel_id', 'overwrite_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "set_channel_permission_overwrite": DiscordHTTPOperation(
    id="set_channel_permission_overwrite",
    method="PUT",
    path="/channels/{channel_id}/permissions/{overwrite_id}",
    input_model=models.DiscordHTTPSetChannelPermissionOverwriteInput,
    path_fields=('channel_id', 'overwrite_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "deprecated_list_pins": DiscordHTTPOperation(
    id="deprecated_list_pins",
    method="GET",
    path="/channels/{channel_id}/pins",
    input_model=models.DiscordHTTPDeprecatedListPinsInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "deprecated_delete_pin": DiscordHTTPOperation(
    id="deprecated_delete_pin",
    method="DELETE",
    path="/channels/{channel_id}/pins/{message_id}",
    input_model=models.DiscordHTTPDeprecatedDeletePinInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "deprecated_create_pin": DiscordHTTPOperation(
    id="deprecated_create_pin",
    method="PUT",
    path="/channels/{channel_id}/pins/{message_id}",
    input_model=models.DiscordHTTPDeprecatedCreatePinInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_answer_voters": DiscordHTTPOperation(
    id="get_answer_voters",
    method="GET",
    path="/channels/{channel_id}/polls/{message_id}/answers/{answer_id}",
    input_model=models.DiscordHTTPGetAnswerVotersInput,
    path_fields=('channel_id', 'message_id', 'answer_id'),
    query_fields=('after', 'limit'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "poll_expire": DiscordHTTPOperation(
    id="poll_expire",
    method="POST",
    path="/channels/{channel_id}/polls/{message_id}/expire",
    input_model=models.DiscordHTTPPollExpireInput,
    path_fields=('channel_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_group_dm_user": DiscordHTTPOperation(
    id="delete_group_dm_user",
    method="DELETE",
    path="/channels/{channel_id}/recipients/{user_id}",
    input_model=models.DiscordHTTPDeleteGroupDmUserInput,
    path_fields=('channel_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "add_group_dm_user": DiscordHTTPOperation(
    id="add_group_dm_user",
    method="PUT",
    path="/channels/{channel_id}/recipients/{user_id}",
    input_model=models.DiscordHTTPAddGroupDmUserInput,
    path_fields=('channel_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201, 204),
  ),
  "send_soundboard_sound": DiscordHTTPOperation(
    id="send_soundboard_sound",
    method="POST",
    path="/channels/{channel_id}/send-soundboard-sound",
    input_model=models.DiscordHTTPSendSoundboardSoundInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "list_thread_members": DiscordHTTPOperation(
    id="list_thread_members",
    method="GET",
    path="/channels/{channel_id}/thread-members",
    input_model=models.DiscordHTTPListThreadMembersInput,
    path_fields=('channel_id',),
    query_fields=('with_member', 'limit', 'after'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "leave_thread": DiscordHTTPOperation(
    id="leave_thread",
    method="DELETE",
    path="/channels/{channel_id}/thread-members/@me",
    input_model=models.DiscordHTTPLeaveThreadInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "join_thread": DiscordHTTPOperation(
    id="join_thread",
    method="PUT",
    path="/channels/{channel_id}/thread-members/@me",
    input_model=models.DiscordHTTPJoinThreadInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "delete_thread_member": DiscordHTTPOperation(
    id="delete_thread_member",
    method="DELETE",
    path="/channels/{channel_id}/thread-members/{user_id}",
    input_model=models.DiscordHTTPDeleteThreadMemberInput,
    path_fields=('channel_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_thread_member": DiscordHTTPOperation(
    id="get_thread_member",
    method="GET",
    path="/channels/{channel_id}/thread-members/{user_id}",
    input_model=models.DiscordHTTPGetThreadMemberInput,
    path_fields=('channel_id', 'user_id'),
    query_fields=('with_member',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "add_thread_member": DiscordHTTPOperation(
    id="add_thread_member",
    method="PUT",
    path="/channels/{channel_id}/thread-members/{user_id}",
    input_model=models.DiscordHTTPAddThreadMemberInput,
    path_fields=('channel_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "create_thread": DiscordHTTPOperation(
    id="create_thread",
    method="POST",
    path="/channels/{channel_id}/threads",
    input_model=models.DiscordHTTPCreateThreadInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(201,),
  ),
  "list_private_archived_threads": DiscordHTTPOperation(
    id="list_private_archived_threads",
    method="GET",
    path="/channels/{channel_id}/threads/archived/private",
    input_model=models.DiscordHTTPListPrivateArchivedThreadsInput,
    path_fields=('channel_id',),
    query_fields=('before', 'limit'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "list_public_archived_threads": DiscordHTTPOperation(
    id="list_public_archived_threads",
    method="GET",
    path="/channels/{channel_id}/threads/archived/public",
    input_model=models.DiscordHTTPListPublicArchivedThreadsInput,
    path_fields=('channel_id',),
    query_fields=('before', 'limit'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "thread_search": DiscordHTTPOperation(
    id="thread_search",
    method="GET",
    path="/channels/{channel_id}/threads/search",
    input_model=models.DiscordHTTPThreadSearchInput,
    path_fields=('channel_id',),
    query_fields=(
      'name',
      'slop',
      'min_id',
      'max_id',
      'tag',
      'tag_setting',
      'archived',
      'sort_by',
      'sort_order',
      'limit',
      'offset',
    ),
    header_fields=(),
    content_types=(),
    success_statuses=(200, 202),
  ),
  "trigger_typing_indicator": DiscordHTTPOperation(
    id="trigger_typing_indicator",
    method="POST",
    path="/channels/{channel_id}/typing",
    input_model=models.DiscordHTTPTriggerTypingIndicatorInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200, 204),
  ),
  "list_my_private_archived_threads": DiscordHTTPOperation(
    id="list_my_private_archived_threads",
    method="GET",
    path="/channels/{channel_id}/users/@me/threads/archived/private",
    input_model=models.DiscordHTTPListMyPrivateArchivedThreadsInput,
    path_fields=('channel_id',),
    query_fields=('before', 'limit'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_voice_channel_status": DiscordHTTPOperation(
    id="update_voice_channel_status",
    method="PUT",
    path="/channels/{channel_id}/voice-status",
    input_model=models.DiscordHTTPUpdateVoiceChannelStatusInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "list_channel_webhooks": DiscordHTTPOperation(
    id="list_channel_webhooks",
    method="GET",
    path="/channels/{channel_id}/webhooks",
    input_model=models.DiscordHTTPListChannelWebhooksInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_webhook": DiscordHTTPOperation(
    id="create_webhook",
    method="POST",
    path="/channels/{channel_id}/webhooks",
    input_model=models.DiscordHTTPCreateWebhookInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_gateway": DiscordHTTPOperation(
    id="get_gateway",
    method="GET",
    path="/gateway",
    input_model=models.DiscordHTTPGetGatewayInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_bot_gateway": DiscordHTTPOperation(
    id="get_bot_gateway",
    method="GET",
    path="/gateway/bot",
    input_model=models.DiscordHTTPGetBotGatewayInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_guild_template": DiscordHTTPOperation(
    id="get_guild_template",
    method="GET",
    path="/guilds/templates/{code}",
    input_model=models.DiscordHTTPGetGuildTemplateInput,
    path_fields=('code',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_guild": DiscordHTTPOperation(
    id="get_guild",
    method="GET",
    path="/guilds/{guild_id}",
    input_model=models.DiscordHTTPGetGuildInput,
    path_fields=('guild_id',),
    query_fields=('with_counts',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild": DiscordHTTPOperation(
    id="update_guild",
    method="PATCH",
    path="/guilds/{guild_id}",
    input_model=models.DiscordHTTPUpdateGuildInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_audit_log_entries": DiscordHTTPOperation(
    id="list_guild_audit_log_entries",
    method="GET",
    path="/guilds/{guild_id}/audit-logs",
    input_model=models.DiscordHTTPListGuildAuditLogEntriesInput,
    path_fields=('guild_id',),
    query_fields=('user_id', 'target_id', 'action_type', 'before', 'after', 'limit'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "list_auto_moderation_rules": DiscordHTTPOperation(
    id="list_auto_moderation_rules",
    method="GET",
    path="/guilds/{guild_id}/auto-moderation/rules",
    input_model=models.DiscordHTTPListAutoModerationRulesInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_auto_moderation_rule": DiscordHTTPOperation(
    id="create_auto_moderation_rule",
    method="POST",
    path="/guilds/{guild_id}/auto-moderation/rules",
    input_model=models.DiscordHTTPCreateAutoModerationRuleInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_auto_moderation_rule": DiscordHTTPOperation(
    id="delete_auto_moderation_rule",
    method="DELETE",
    path="/guilds/{guild_id}/auto-moderation/rules/{rule_id}",
    input_model=models.DiscordHTTPDeleteAutoModerationRuleInput,
    path_fields=('guild_id', 'rule_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_auto_moderation_rule": DiscordHTTPOperation(
    id="get_auto_moderation_rule",
    method="GET",
    path="/guilds/{guild_id}/auto-moderation/rules/{rule_id}",
    input_model=models.DiscordHTTPGetAutoModerationRuleInput,
    path_fields=('guild_id', 'rule_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_auto_moderation_rule": DiscordHTTPOperation(
    id="update_auto_moderation_rule",
    method="PATCH",
    path="/guilds/{guild_id}/auto-moderation/rules/{rule_id}",
    input_model=models.DiscordHTTPUpdateAutoModerationRuleInput,
    path_fields=('guild_id', 'rule_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_bans": DiscordHTTPOperation(
    id="list_guild_bans",
    method="GET",
    path="/guilds/{guild_id}/bans",
    input_model=models.DiscordHTTPListGuildBansInput,
    path_fields=('guild_id',),
    query_fields=('limit', 'before', 'after'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "unban_user_from_guild": DiscordHTTPOperation(
    id="unban_user_from_guild",
    method="DELETE",
    path="/guilds/{guild_id}/bans/{user_id}",
    input_model=models.DiscordHTTPUnbanUserFromGuildInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "get_guild_ban": DiscordHTTPOperation(
    id="get_guild_ban",
    method="GET",
    path="/guilds/{guild_id}/bans/{user_id}",
    input_model=models.DiscordHTTPGetGuildBanInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "ban_user_from_guild": DiscordHTTPOperation(
    id="ban_user_from_guild",
    method="PUT",
    path="/guilds/{guild_id}/bans/{user_id}",
    input_model=models.DiscordHTTPBanUserFromGuildInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "bulk_ban_users_from_guild": DiscordHTTPOperation(
    id="bulk_ban_users_from_guild",
    method="POST",
    path="/guilds/{guild_id}/bulk-ban",
    input_model=models.DiscordHTTPBulkBanUsersFromGuildInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_channels": DiscordHTTPOperation(
    id="list_guild_channels",
    method="GET",
    path="/guilds/{guild_id}/channels",
    input_model=models.DiscordHTTPListGuildChannelsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "bulk_update_guild_channels": DiscordHTTPOperation(
    id="bulk_update_guild_channels",
    method="PATCH",
    path="/guilds/{guild_id}/channels",
    input_model=models.DiscordHTTPBulkUpdateGuildChannelsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "create_guild_channel": DiscordHTTPOperation(
    id="create_guild_channel",
    method="POST",
    path="/guilds/{guild_id}/channels",
    input_model=models.DiscordHTTPCreateGuildChannelInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201,),
  ),
  "list_guild_emojis": DiscordHTTPOperation(
    id="list_guild_emojis",
    method="GET",
    path="/guilds/{guild_id}/emojis",
    input_model=models.DiscordHTTPListGuildEmojisInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_guild_emoji": DiscordHTTPOperation(
    id="create_guild_emoji",
    method="POST",
    path="/guilds/{guild_id}/emojis",
    input_model=models.DiscordHTTPCreateGuildEmojiInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201,),
  ),
  "delete_guild_emoji": DiscordHTTPOperation(
    id="delete_guild_emoji",
    method="DELETE",
    path="/guilds/{guild_id}/emojis/{emoji_id}",
    input_model=models.DiscordHTTPDeleteGuildEmojiInput,
    path_fields=('guild_id', 'emoji_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_guild_emoji": DiscordHTTPOperation(
    id="get_guild_emoji",
    method="GET",
    path="/guilds/{guild_id}/emojis/{emoji_id}",
    input_model=models.DiscordHTTPGetGuildEmojiInput,
    path_fields=('guild_id', 'emoji_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_emoji": DiscordHTTPOperation(
    id="update_guild_emoji",
    method="PATCH",
    path="/guilds/{guild_id}/emojis/{emoji_id}",
    input_model=models.DiscordHTTPUpdateGuildEmojiInput,
    path_fields=('guild_id', 'emoji_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "update_guild_incident_actions": DiscordHTTPOperation(
    id="update_guild_incident_actions",
    method="PUT",
    path="/guilds/{guild_id}/incident-actions",
    input_model=models.DiscordHTTPUpdateGuildIncidentActionsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_integrations": DiscordHTTPOperation(
    id="list_guild_integrations",
    method="GET",
    path="/guilds/{guild_id}/integrations",
    input_model=models.DiscordHTTPListGuildIntegrationsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_guild_integration": DiscordHTTPOperation(
    id="delete_guild_integration",
    method="DELETE",
    path="/guilds/{guild_id}/integrations/{integration_id}",
    input_model=models.DiscordHTTPDeleteGuildIntegrationInput,
    path_fields=('guild_id', 'integration_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "list_guild_invites": DiscordHTTPOperation(
    id="list_guild_invites",
    method="GET",
    path="/guilds/{guild_id}/invites",
    input_model=models.DiscordHTTPListGuildInvitesInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "list_guild_members": DiscordHTTPOperation(
    id="list_guild_members",
    method="GET",
    path="/guilds/{guild_id}/members",
    input_model=models.DiscordHTTPListGuildMembersInput,
    path_fields=('guild_id',),
    query_fields=('limit', 'after'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_my_guild_member": DiscordHTTPOperation(
    id="update_my_guild_member",
    method="PATCH",
    path="/guilds/{guild_id}/members/@me",
    input_model=models.DiscordHTTPUpdateMyGuildMemberInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "search_guild_members": DiscordHTTPOperation(
    id="search_guild_members",
    method="GET",
    path="/guilds/{guild_id}/members/search",
    input_model=models.DiscordHTTPSearchGuildMembersInput,
    path_fields=('guild_id',),
    query_fields=('limit', 'query'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_guild_member": DiscordHTTPOperation(
    id="delete_guild_member",
    method="DELETE",
    path="/guilds/{guild_id}/members/{user_id}",
    input_model=models.DiscordHTTPDeleteGuildMemberInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_guild_member": DiscordHTTPOperation(
    id="get_guild_member",
    method="GET",
    path="/guilds/{guild_id}/members/{user_id}",
    input_model=models.DiscordHTTPGetGuildMemberInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_member": DiscordHTTPOperation(
    id="update_guild_member",
    method="PATCH",
    path="/guilds/{guild_id}/members/{user_id}",
    input_model=models.DiscordHTTPUpdateGuildMemberInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200, 204),
  ),
  "add_guild_member": DiscordHTTPOperation(
    id="add_guild_member",
    method="PUT",
    path="/guilds/{guild_id}/members/{user_id}",
    input_model=models.DiscordHTTPAddGuildMemberInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201, 204),
  ),
  "delete_guild_member_role": DiscordHTTPOperation(
    id="delete_guild_member_role",
    method="DELETE",
    path="/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
    input_model=models.DiscordHTTPDeleteGuildMemberRoleInput,
    path_fields=('guild_id', 'user_id', 'role_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "add_guild_member_role": DiscordHTTPOperation(
    id="add_guild_member_role",
    method="PUT",
    path="/guilds/{guild_id}/members/{user_id}/roles/{role_id}",
    input_model=models.DiscordHTTPAddGuildMemberRoleInput,
    path_fields=('guild_id', 'user_id', 'role_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "guild_search": DiscordHTTPOperation(
    id="guild_search",
    method="GET",
    path="/guilds/{guild_id}/messages/search",
    input_model=models.DiscordHTTPGuildSearchInput,
    path_fields=('guild_id',),
    query_fields=(
      'sort_by',
      'sort_order',
      'content',
      'slop',
      'author_id',
      'author_type',
      'mentions',
      'mentions_role_id',
      'replied_to_user_id',
      'replied_to_message_id',
      'mention_everyone',
      'min_id',
      'max_id',
      'limit',
      'offset',
      'has',
      'link_hostname',
      'embed_provider',
      'embed_type',
      'attachment_extension',
      'attachment_filename',
      'pinned',
      'include_nsfw',
      'channel_id',
    ),
    header_fields=(),
    content_types=(),
    success_statuses=(200, 202),
  ),
  "get_guild_new_member_welcome": DiscordHTTPOperation(
    id="get_guild_new_member_welcome",
    method="GET",
    path="/guilds/{guild_id}/new-member-welcome",
    input_model=models.DiscordHTTPGetGuildNewMemberWelcomeInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200, 204),
  ),
  "get_guilds_onboarding": DiscordHTTPOperation(
    id="get_guilds_onboarding",
    method="GET",
    path="/guilds/{guild_id}/onboarding",
    input_model=models.DiscordHTTPGetGuildsOnboardingInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "put_guilds_onboarding": DiscordHTTPOperation(
    id="put_guilds_onboarding",
    method="PUT",
    path="/guilds/{guild_id}/onboarding",
    input_model=models.DiscordHTTPPutGuildsOnboardingInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_guild_preview": DiscordHTTPOperation(
    id="get_guild_preview",
    method="GET",
    path="/guilds/{guild_id}/preview",
    input_model=models.DiscordHTTPGetGuildPreviewInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "preview_prune_guild": DiscordHTTPOperation(
    id="preview_prune_guild",
    method="GET",
    path="/guilds/{guild_id}/prune",
    input_model=models.DiscordHTTPPreviewPruneGuildInput,
    path_fields=('guild_id',),
    query_fields=('days', 'include_roles'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "prune_guild": DiscordHTTPOperation(
    id="prune_guild",
    method="POST",
    path="/guilds/{guild_id}/prune",
    input_model=models.DiscordHTTPPruneGuildInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_voice_regions": DiscordHTTPOperation(
    id="list_guild_voice_regions",
    method="GET",
    path="/guilds/{guild_id}/regions",
    input_model=models.DiscordHTTPListGuildVoiceRegionsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_guild_join_requests": DiscordHTTPOperation(
    id="get_guild_join_requests",
    method="GET",
    path="/guilds/{guild_id}/requests",
    input_model=models.DiscordHTTPGetGuildJoinRequestsInput,
    path_fields=('guild_id',),
    query_fields=('status', 'limit', 'before', 'after'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "action_guild_join_request": DiscordHTTPOperation(
    id="action_guild_join_request",
    method="PATCH",
    path="/guilds/{guild_id}/requests/{request_id}",
    input_model=models.DiscordHTTPActionGuildJoinRequestInput,
    path_fields=('guild_id', 'request_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_roles": DiscordHTTPOperation(
    id="list_guild_roles",
    method="GET",
    path="/guilds/{guild_id}/roles",
    input_model=models.DiscordHTTPListGuildRolesInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "bulk_update_guild_roles": DiscordHTTPOperation(
    id="bulk_update_guild_roles",
    method="PATCH",
    path="/guilds/{guild_id}/roles",
    input_model=models.DiscordHTTPBulkUpdateGuildRolesInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "create_guild_role": DiscordHTTPOperation(
    id="create_guild_role",
    method="POST",
    path="/guilds/{guild_id}/roles",
    input_model=models.DiscordHTTPCreateGuildRoleInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "guild_role_member_counts": DiscordHTTPOperation(
    id="guild_role_member_counts",
    method="GET",
    path="/guilds/{guild_id}/roles/member-counts",
    input_model=models.DiscordHTTPGuildRoleMemberCountsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_guild_role": DiscordHTTPOperation(
    id="delete_guild_role",
    method="DELETE",
    path="/guilds/{guild_id}/roles/{role_id}",
    input_model=models.DiscordHTTPDeleteGuildRoleInput,
    path_fields=('guild_id', 'role_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_guild_role": DiscordHTTPOperation(
    id="get_guild_role",
    method="GET",
    path="/guilds/{guild_id}/roles/{role_id}",
    input_model=models.DiscordHTTPGetGuildRoleInput,
    path_fields=('guild_id', 'role_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_role": DiscordHTTPOperation(
    id="update_guild_role",
    method="PATCH",
    path="/guilds/{guild_id}/roles/{role_id}",
    input_model=models.DiscordHTTPUpdateGuildRoleInput,
    path_fields=('guild_id', 'role_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_scheduled_events": DiscordHTTPOperation(
    id="list_guild_scheduled_events",
    method="GET",
    path="/guilds/{guild_id}/scheduled-events",
    input_model=models.DiscordHTTPListGuildScheduledEventsInput,
    path_fields=('guild_id',),
    query_fields=('with_user_count',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_guild_scheduled_event": DiscordHTTPOperation(
    id="create_guild_scheduled_event",
    method="POST",
    path="/guilds/{guild_id}/scheduled-events",
    input_model=models.DiscordHTTPCreateGuildScheduledEventInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_guild_scheduled_event": DiscordHTTPOperation(
    id="delete_guild_scheduled_event",
    method="DELETE",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}",
    input_model=models.DiscordHTTPDeleteGuildScheduledEventInput,
    path_fields=('guild_id', 'guild_scheduled_event_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_guild_scheduled_event": DiscordHTTPOperation(
    id="get_guild_scheduled_event",
    method="GET",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}",
    input_model=models.DiscordHTTPGetGuildScheduledEventInput,
    path_fields=('guild_id', 'guild_scheduled_event_id'),
    query_fields=('with_user_count',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_scheduled_event": DiscordHTTPOperation(
    id="update_guild_scheduled_event",
    method="PATCH",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}",
    input_model=models.DiscordHTTPUpdateGuildScheduledEventInput,
    path_fields=('guild_id', 'guild_scheduled_event_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "create_guild_scheduled_event_exception": DiscordHTTPOperation(
    id="create_guild_scheduled_event_exception",
    method="POST",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}/exceptions",
    input_model=models.DiscordHTTPCreateGuildScheduledEventExceptionInput,
    path_fields=('guild_id', 'guild_scheduled_event_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_guild_scheduled_event_exception": DiscordHTTPOperation(
    id="delete_guild_scheduled_event_exception",
    method="DELETE",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}/exceptions/{exception_id}",
    input_model=models.DiscordHTTPDeleteGuildScheduledEventExceptionInput,
    path_fields=('guild_id', 'guild_scheduled_event_id', 'exception_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "update_guild_scheduled_event_exception": DiscordHTTPOperation(
    id="update_guild_scheduled_event_exception",
    method="PATCH",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}/exceptions/{exception_id}",
    input_model=models.DiscordHTTPUpdateGuildScheduledEventExceptionInput,
    path_fields=('guild_id', 'guild_scheduled_event_id', 'exception_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_scheduled_event_users": DiscordHTTPOperation(
    id="list_guild_scheduled_event_users",
    method="GET",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}/users",
    input_model=models.DiscordHTTPListGuildScheduledEventUsersInput,
    path_fields=('guild_id', 'guild_scheduled_event_id'),
    query_fields=('with_member', 'limit', 'before', 'after'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "count_guild_scheduled_event_users": DiscordHTTPOperation(
    id="count_guild_scheduled_event_users",
    method="GET",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}/users/counts",
    input_model=models.DiscordHTTPCountGuildScheduledEventUsersInput,
    path_fields=('guild_id', 'guild_scheduled_event_id'),
    query_fields=('guild_scheduled_event_exception_ids',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "list_guild_scheduled_event_exception_users": DiscordHTTPOperation(
    id="list_guild_scheduled_event_exception_users",
    method="GET",
    path="/guilds/{guild_id}/scheduled-events/{guild_scheduled_event_id}/{guild_scheduled_event_exception_id}/users",
    input_model=models.DiscordHTTPListGuildScheduledEventExceptionUsersInput,
    path_fields=(
      'guild_id',
      'guild_scheduled_event_id',
      'guild_scheduled_event_exception_id',
    ),
    query_fields=('with_member', 'limit', 'before', 'after'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "list_guild_soundboard_sounds": DiscordHTTPOperation(
    id="list_guild_soundboard_sounds",
    method="GET",
    path="/guilds/{guild_id}/soundboard-sounds",
    input_model=models.DiscordHTTPListGuildSoundboardSoundsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_guild_soundboard_sound": DiscordHTTPOperation(
    id="create_guild_soundboard_sound",
    method="POST",
    path="/guilds/{guild_id}/soundboard-sounds",
    input_model=models.DiscordHTTPCreateGuildSoundboardSoundInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201,),
  ),
  "delete_guild_soundboard_sound": DiscordHTTPOperation(
    id="delete_guild_soundboard_sound",
    method="DELETE",
    path="/guilds/{guild_id}/soundboard-sounds/{sound_id}",
    input_model=models.DiscordHTTPDeleteGuildSoundboardSoundInput,
    path_fields=('guild_id', 'sound_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_guild_soundboard_sound": DiscordHTTPOperation(
    id="get_guild_soundboard_sound",
    method="GET",
    path="/guilds/{guild_id}/soundboard-sounds/{sound_id}",
    input_model=models.DiscordHTTPGetGuildSoundboardSoundInput,
    path_fields=('guild_id', 'sound_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_soundboard_sound": DiscordHTTPOperation(
    id="update_guild_soundboard_sound",
    method="PATCH",
    path="/guilds/{guild_id}/soundboard-sounds/{sound_id}",
    input_model=models.DiscordHTTPUpdateGuildSoundboardSoundInput,
    path_fields=('guild_id', 'sound_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_stickers": DiscordHTTPOperation(
    id="list_guild_stickers",
    method="GET",
    path="/guilds/{guild_id}/stickers",
    input_model=models.DiscordHTTPListGuildStickersInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_guild_sticker": DiscordHTTPOperation(
    id="create_guild_sticker",
    method="POST",
    path="/guilds/{guild_id}/stickers",
    input_model=models.DiscordHTTPCreateGuildStickerInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('multipart/form-data',),
    success_statuses=(201,),
  ),
  "delete_guild_sticker": DiscordHTTPOperation(
    id="delete_guild_sticker",
    method="DELETE",
    path="/guilds/{guild_id}/stickers/{sticker_id}",
    input_model=models.DiscordHTTPDeleteGuildStickerInput,
    path_fields=('guild_id', 'sticker_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_guild_sticker": DiscordHTTPOperation(
    id="get_guild_sticker",
    method="GET",
    path="/guilds/{guild_id}/stickers/{sticker_id}",
    input_model=models.DiscordHTTPGetGuildStickerInput,
    path_fields=('guild_id', 'sticker_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_sticker": DiscordHTTPOperation(
    id="update_guild_sticker",
    method="PATCH",
    path="/guilds/{guild_id}/stickers/{sticker_id}",
    input_model=models.DiscordHTTPUpdateGuildStickerInput,
    path_fields=('guild_id', 'sticker_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_guild_templates": DiscordHTTPOperation(
    id="list_guild_templates",
    method="GET",
    path="/guilds/{guild_id}/templates",
    input_model=models.DiscordHTTPListGuildTemplatesInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_guild_template": DiscordHTTPOperation(
    id="create_guild_template",
    method="POST",
    path="/guilds/{guild_id}/templates",
    input_model=models.DiscordHTTPCreateGuildTemplateInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_guild_template": DiscordHTTPOperation(
    id="delete_guild_template",
    method="DELETE",
    path="/guilds/{guild_id}/templates/{code}",
    input_model=models.DiscordHTTPDeleteGuildTemplateInput,
    path_fields=('guild_id', 'code'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_template": DiscordHTTPOperation(
    id="update_guild_template",
    method="PATCH",
    path="/guilds/{guild_id}/templates/{code}",
    input_model=models.DiscordHTTPUpdateGuildTemplateInput,
    path_fields=('guild_id', 'code'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "sync_guild_template": DiscordHTTPOperation(
    id="sync_guild_template",
    method="PUT",
    path="/guilds/{guild_id}/templates/{code}",
    input_model=models.DiscordHTTPSyncGuildTemplateInput,
    path_fields=('guild_id', 'code'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_active_guild_threads": DiscordHTTPOperation(
    id="get_active_guild_threads",
    method="GET",
    path="/guilds/{guild_id}/threads/active",
    input_model=models.DiscordHTTPGetActiveGuildThreadsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_guild_vanity_url": DiscordHTTPOperation(
    id="get_guild_vanity_url",
    method="GET",
    path="/guilds/{guild_id}/vanity-url",
    input_model=models.DiscordHTTPGetGuildVanityUrlInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_self_voice_state": DiscordHTTPOperation(
    id="get_self_voice_state",
    method="GET",
    path="/guilds/{guild_id}/voice-states/@me",
    input_model=models.DiscordHTTPGetSelfVoiceStateInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_self_voice_state": DiscordHTTPOperation(
    id="update_self_voice_state",
    method="PATCH",
    path="/guilds/{guild_id}/voice-states/@me",
    input_model=models.DiscordHTTPUpdateSelfVoiceStateInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "get_voice_state": DiscordHTTPOperation(
    id="get_voice_state",
    method="GET",
    path="/guilds/{guild_id}/voice-states/{user_id}",
    input_model=models.DiscordHTTPGetVoiceStateInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_voice_state": DiscordHTTPOperation(
    id="update_voice_state",
    method="PATCH",
    path="/guilds/{guild_id}/voice-states/{user_id}",
    input_model=models.DiscordHTTPUpdateVoiceStateInput,
    path_fields=('guild_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "get_guild_webhooks": DiscordHTTPOperation(
    id="get_guild_webhooks",
    method="GET",
    path="/guilds/{guild_id}/webhooks",
    input_model=models.DiscordHTTPGetGuildWebhooksInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_guild_welcome_screen": DiscordHTTPOperation(
    id="get_guild_welcome_screen",
    method="GET",
    path="/guilds/{guild_id}/welcome-screen",
    input_model=models.DiscordHTTPGetGuildWelcomeScreenInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_welcome_screen": DiscordHTTPOperation(
    id="update_guild_welcome_screen",
    method="PATCH",
    path="/guilds/{guild_id}/welcome-screen",
    input_model=models.DiscordHTTPUpdateGuildWelcomeScreenInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_guild_widget_settings": DiscordHTTPOperation(
    id="get_guild_widget_settings",
    method="GET",
    path="/guilds/{guild_id}/widget",
    input_model=models.DiscordHTTPGetGuildWidgetSettingsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_guild_widget_settings": DiscordHTTPOperation(
    id="update_guild_widget_settings",
    method="PATCH",
    path="/guilds/{guild_id}/widget",
    input_model=models.DiscordHTTPUpdateGuildWidgetSettingsInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_guild_widget": DiscordHTTPOperation(
    id="get_guild_widget",
    method="GET",
    path="/guilds/{guild_id}/widget.json",
    input_model=models.DiscordHTTPGetGuildWidgetInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_guild_widget_png": DiscordHTTPOperation(
    id="get_guild_widget_png",
    method="GET",
    path="/guilds/{guild_id}/widget.png",
    input_model=models.DiscordHTTPGetGuildWidgetPngInput,
    path_fields=('guild_id',),
    query_fields=('style',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_interaction_response": DiscordHTTPOperation(
    id="create_interaction_response",
    method="POST",
    path="/interactions/{interaction_id}/{interaction_token}/callback",
    input_model=models.DiscordHTTPCreateInteractionResponseInput,
    path_fields=('interaction_id', 'interaction_token'),
    query_fields=('with_response',),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200, 204),
  ),
  "invite_revoke": DiscordHTTPOperation(
    id="invite_revoke",
    method="DELETE",
    path="/invites/{code}",
    input_model=models.DiscordHTTPInviteRevokeInput,
    path_fields=('code',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "invite_resolve": DiscordHTTPOperation(
    id="invite_resolve",
    method="GET",
    path="/invites/{code}",
    input_model=models.DiscordHTTPInviteResolveInput,
    path_fields=('code',),
    query_fields=(
      'with_counts',
      'guild_scheduled_event_id',
      'target_channel_id',
      'target_message_id',
    ),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_invite_target_users": DiscordHTTPOperation(
    id="get_invite_target_users",
    method="GET",
    path="/invites/{code}/target-users",
    input_model=models.DiscordHTTPGetInviteTargetUsersInput,
    path_fields=('code',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_invite_target_users": DiscordHTTPOperation(
    id="update_invite_target_users",
    method="PUT",
    path="/invites/{code}/target-users",
    input_model=models.DiscordHTTPUpdateInviteTargetUsersInput,
    path_fields=('code',),
    query_fields=(),
    header_fields=(),
    content_types=('multipart/form-data',),
    success_statuses=(204,),
  ),
  "get_invite_target_users_job_status": DiscordHTTPOperation(
    id="get_invite_target_users_job_status",
    method="GET",
    path="/invites/{code}/target-users/job-status",
    input_model=models.DiscordHTTPGetInviteTargetUsersJobStatusInput,
    path_fields=('code',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_lobby": DiscordHTTPOperation(
    id="create_lobby",
    method="POST",
    path="/lobbies",
    input_model=models.DiscordHTTPCreateLobbyInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(201,),
  ),
  "create_or_join_lobby": DiscordHTTPOperation(
    id="create_or_join_lobby",
    method="PUT",
    path="/lobbies",
    input_model=models.DiscordHTTPCreateOrJoinLobbyInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_lobby": DiscordHTTPOperation(
    id="delete_lobby",
    method="DELETE",
    path="/lobbies/{lobby_id}",
    input_model=models.DiscordHTTPDeleteLobbyInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_lobby": DiscordHTTPOperation(
    id="get_lobby",
    method="GET",
    path="/lobbies/{lobby_id}",
    input_model=models.DiscordHTTPGetLobbyInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "edit_lobby": DiscordHTTPOperation(
    id="edit_lobby",
    method="PATCH",
    path="/lobbies/{lobby_id}",
    input_model=models.DiscordHTTPEditLobbyInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "edit_lobby_channel_link": DiscordHTTPOperation(
    id="edit_lobby_channel_link",
    method="PATCH",
    path="/lobbies/{lobby_id}/channel-linking",
    input_model=models.DiscordHTTPEditLobbyChannelLinkInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "leave_lobby": DiscordHTTPOperation(
    id="leave_lobby",
    method="DELETE",
    path="/lobbies/{lobby_id}/members/@me",
    input_model=models.DiscordHTTPLeaveLobbyInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "create_linked_lobby_guild_invite_for_self": DiscordHTTPOperation(
    id="create_linked_lobby_guild_invite_for_self",
    method="POST",
    path="/lobbies/{lobby_id}/members/@me/invites",
    input_model=models.DiscordHTTPCreateLinkedLobbyGuildInviteForSelfInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "bulk_update_lobby_members": DiscordHTTPOperation(
    id="bulk_update_lobby_members",
    method="POST",
    path="/lobbies/{lobby_id}/members/bulk",
    input_model=models.DiscordHTTPBulkUpdateLobbyMembersInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_lobby_member": DiscordHTTPOperation(
    id="delete_lobby_member",
    method="DELETE",
    path="/lobbies/{lobby_id}/members/{user_id}",
    input_model=models.DiscordHTTPDeleteLobbyMemberInput,
    path_fields=('lobby_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "add_lobby_member": DiscordHTTPOperation(
    id="add_lobby_member",
    method="PUT",
    path="/lobbies/{lobby_id}/members/{user_id}",
    input_model=models.DiscordHTTPAddLobbyMemberInput,
    path_fields=('lobby_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "create_linked_lobby_guild_invite_for_user": DiscordHTTPOperation(
    id="create_linked_lobby_guild_invite_for_user",
    method="POST",
    path="/lobbies/{lobby_id}/members/{user_id}/invites",
    input_model=models.DiscordHTTPCreateLinkedLobbyGuildInviteForUserInput,
    path_fields=('lobby_id', 'user_id'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_lobby_messages": DiscordHTTPOperation(
    id="get_lobby_messages",
    method="GET",
    path="/lobbies/{lobby_id}/messages",
    input_model=models.DiscordHTTPGetLobbyMessagesInput,
    path_fields=('lobby_id',),
    query_fields=('limit',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_lobby_message": DiscordHTTPOperation(
    id="create_lobby_message",
    method="POST",
    path="/lobbies/{lobby_id}/messages",
    input_model=models.DiscordHTTPCreateLobbyMessageInput,
    path_fields=('lobby_id',),
    query_fields=(),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(201,),
  ),
  "update_lobby_message_external_moderation_metadata": DiscordHTTPOperation(
    id="update_lobby_message_external_moderation_metadata",
    method="PUT",
    path="/lobbies/{lobby_id}/messages/{message_id}/moderation-metadata",
    input_model=models.DiscordHTTPUpdateLobbyMessageExternalModerationMetadataInput,
    path_fields=('lobby_id', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(204,),
  ),
  "get_my_oauth2_authorization": DiscordHTTPOperation(
    id="get_my_oauth2_authorization",
    method="GET",
    path="/oauth2/@me",
    input_model=models.DiscordHTTPGetMyOauth2AuthorizationInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_my_oauth2_application": DiscordHTTPOperation(
    id="get_my_oauth2_application",
    method="GET",
    path="/oauth2/applications/@me",
    input_model=models.DiscordHTTPGetMyOauth2ApplicationInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_public_keys": DiscordHTTPOperation(
    id="get_public_keys",
    method="GET",
    path="/oauth2/keys",
    input_model=models.DiscordHTTPGetPublicKeysInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_openid_connect_userinfo": DiscordHTTPOperation(
    id="get_openid_connect_userinfo",
    method="GET",
    path="/oauth2/userinfo",
    input_model=models.DiscordHTTPGetOpenidConnectUserinfoInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_user_message_external_moderation_metadata": DiscordHTTPOperation(
    id="update_user_message_external_moderation_metadata",
    method="PUT",
    path="/partner-sdk/dms/{user_id_1}/{user_id_2}/messages/{message_id}/moderation-metadata",
    input_model=models.DiscordHTTPUpdateUserMessageExternalModerationMetadataInput,
    path_fields=('user_id_1', 'user_id_2', 'message_id'),
    query_fields=(),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(204,),
  ),
  "partner_sdk_unmerge_provisional_account": DiscordHTTPOperation(
    id="partner_sdk_unmerge_provisional_account",
    method="POST",
    path="/partner-sdk/provisional-accounts/unmerge",
    input_model=models.DiscordHTTPPartnerSdkUnmergeProvisionalAccountInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "bot_partner_sdk_unmerge_provisional_account": DiscordHTTPOperation(
    id="bot_partner_sdk_unmerge_provisional_account",
    method="POST",
    path="/partner-sdk/provisional-accounts/unmerge/bot",
    input_model=models.DiscordHTTPBotPartnerSdkUnmergeProvisionalAccountInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "partner_sdk_token": DiscordHTTPOperation(
    id="partner_sdk_token",
    method="POST",
    path="/partner-sdk/token",
    input_model=models.DiscordHTTPPartnerSdkTokenInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "bot_partner_sdk_token": DiscordHTTPOperation(
    id="bot_partner_sdk_token",
    method="POST",
    path="/partner-sdk/token/bot",
    input_model=models.DiscordHTTPBotPartnerSdkTokenInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_sku_subscriptions": DiscordHTTPOperation(
    id="get_sku_subscriptions",
    method="GET",
    path="/skus/{sku_id}/subscriptions",
    input_model=models.DiscordHTTPGetSkuSubscriptionsInput,
    path_fields=('sku_id',),
    query_fields=('before', 'after', 'limit', 'user_id'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_sku_subscription": DiscordHTTPOperation(
    id="get_sku_subscription",
    method="GET",
    path="/skus/{sku_id}/subscriptions/{subscription_id}",
    input_model=models.DiscordHTTPGetSkuSubscriptionInput,
    path_fields=('sku_id', 'subscription_id'),
    query_fields=('user_id',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_soundboard_default_sounds": DiscordHTTPOperation(
    id="get_soundboard_default_sounds",
    method="GET",
    path="/soundboard-default-sounds",
    input_model=models.DiscordHTTPGetSoundboardDefaultSoundsInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "create_stage_instance": DiscordHTTPOperation(
    id="create_stage_instance",
    method="POST",
    path="/stage-instances",
    input_model=models.DiscordHTTPCreateStageInstanceInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_stage_instance": DiscordHTTPOperation(
    id="delete_stage_instance",
    method="DELETE",
    path="/stage-instances/{channel_id}",
    input_model=models.DiscordHTTPDeleteStageInstanceInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_stage_instance": DiscordHTTPOperation(
    id="get_stage_instance",
    method="GET",
    path="/stage-instances/{channel_id}",
    input_model=models.DiscordHTTPGetStageInstanceInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_stage_instance": DiscordHTTPOperation(
    id="update_stage_instance",
    method="PATCH",
    path="/stage-instances/{channel_id}",
    input_model=models.DiscordHTTPUpdateStageInstanceInput,
    path_fields=('channel_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_sticker_packs": DiscordHTTPOperation(
    id="list_sticker_packs",
    method="GET",
    path="/sticker-packs",
    input_model=models.DiscordHTTPListStickerPacksInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_sticker_pack": DiscordHTTPOperation(
    id="get_sticker_pack",
    method="GET",
    path="/sticker-packs/{pack_id}",
    input_model=models.DiscordHTTPGetStickerPackInput,
    path_fields=('pack_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_sticker": DiscordHTTPOperation(
    id="get_sticker",
    method="GET",
    path="/stickers/{sticker_id}",
    input_model=models.DiscordHTTPGetStickerInput,
    path_fields=('sticker_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_my_user": DiscordHTTPOperation(
    id="get_my_user",
    method="GET",
    path="/users/@me",
    input_model=models.DiscordHTTPGetMyUserInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_my_user": DiscordHTTPOperation(
    id="update_my_user",
    method="PATCH",
    path="/users/@me",
    input_model=models.DiscordHTTPUpdateMyUserInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "get_current_user_application_entitlements": DiscordHTTPOperation(
    id="get_current_user_application_entitlements",
    method="GET",
    path="/users/@me/applications/{application_id}/entitlements",
    input_model=models.DiscordHTTPGetCurrentUserApplicationEntitlementsInput,
    path_fields=('application_id',),
    query_fields=('sku_ids', 'exclude_consumed'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_application_user_role_connection": DiscordHTTPOperation(
    id="delete_application_user_role_connection",
    method="DELETE",
    path="/users/@me/applications/{application_id}/role-connection",
    input_model=models.DiscordHTTPDeleteApplicationUserRoleConnectionInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_application_user_role_connection": DiscordHTTPOperation(
    id="get_application_user_role_connection",
    method="GET",
    path="/users/@me/applications/{application_id}/role-connection",
    input_model=models.DiscordHTTPGetApplicationUserRoleConnectionInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_application_user_role_connection": DiscordHTTPOperation(
    id="update_application_user_role_connection",
    method="PUT",
    path="/users/@me/applications/{application_id}/role-connection",
    input_model=models.DiscordHTTPUpdateApplicationUserRoleConnectionInput,
    path_fields=('application_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "create_dm": DiscordHTTPOperation(
    id="create_dm",
    method="POST",
    path="/users/@me/channels",
    input_model=models.DiscordHTTPCreateDmInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "list_my_connections": DiscordHTTPOperation(
    id="list_my_connections",
    method="GET",
    path="/users/@me/connections",
    input_model=models.DiscordHTTPListMyConnectionsInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "list_my_guilds": DiscordHTTPOperation(
    id="list_my_guilds",
    method="GET",
    path="/users/@me/guilds",
    input_model=models.DiscordHTTPListMyGuildsInput,
    path_fields=(),
    query_fields=('before', 'after', 'limit', 'with_counts'),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "leave_guild": DiscordHTTPOperation(
    id="leave_guild",
    method="DELETE",
    path="/users/@me/guilds/{guild_id}",
    input_model=models.DiscordHTTPLeaveGuildInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_my_guild_member": DiscordHTTPOperation(
    id="get_my_guild_member",
    method="GET",
    path="/users/@me/guilds/{guild_id}/member",
    input_model=models.DiscordHTTPGetMyGuildMemberInput,
    path_fields=('guild_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "get_user": DiscordHTTPOperation(
    id="get_user",
    method="GET",
    path="/users/{user_id}",
    input_model=models.DiscordHTTPGetUserInput,
    path_fields=('user_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "list_voice_regions": DiscordHTTPOperation(
    id="list_voice_regions",
    method="GET",
    path="/voice/regions",
    input_model=models.DiscordHTTPListVoiceRegionsInput,
    path_fields=(),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "delete_webhook": DiscordHTTPOperation(
    id="delete_webhook",
    method="DELETE",
    path="/webhooks/{webhook_id}",
    input_model=models.DiscordHTTPDeleteWebhookInput,
    path_fields=('webhook_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_webhook": DiscordHTTPOperation(
    id="get_webhook",
    method="GET",
    path="/webhooks/{webhook_id}",
    input_model=models.DiscordHTTPGetWebhookInput,
    path_fields=('webhook_id',),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_webhook": DiscordHTTPOperation(
    id="update_webhook",
    method="PATCH",
    path="/webhooks/{webhook_id}",
    input_model=models.DiscordHTTPUpdateWebhookInput,
    path_fields=('webhook_id',),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "delete_webhook_by_token": DiscordHTTPOperation(
    id="delete_webhook_by_token",
    method="DELETE",
    path="/webhooks/{webhook_id}/{webhook_token}",
    input_model=models.DiscordHTTPDeleteWebhookByTokenInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_webhook_by_token": DiscordHTTPOperation(
    id="get_webhook_by_token",
    method="GET",
    path="/webhooks/{webhook_id}/{webhook_token}",
    input_model=models.DiscordHTTPGetWebhookByTokenInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=(),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_webhook_by_token": DiscordHTTPOperation(
    id="update_webhook_by_token",
    method="PATCH",
    path="/webhooks/{webhook_id}/{webhook_token}",
    input_model=models.DiscordHTTPUpdateWebhookByTokenInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=(),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(200,),
  ),
  "execute_webhook": DiscordHTTPOperation(
    id="execute_webhook",
    method="POST",
    path="/webhooks/{webhook_id}/{webhook_token}",
    input_model=models.DiscordHTTPExecuteWebhookInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=('wait', 'thread_id', 'with_components'),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200, 204),
  ),
  "execute_github_compatible_webhook": DiscordHTTPOperation(
    id="execute_github_compatible_webhook",
    method="POST",
    path="/webhooks/{webhook_id}/{webhook_token}/github",
    input_model=models.DiscordHTTPExecuteGithubCompatibleWebhookInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=('wait', 'thread_id'),
    header_fields=(),
    content_types=('application/json',),
    success_statuses=(204,),
  ),
  "delete_original_webhook_message": DiscordHTTPOperation(
    id="delete_original_webhook_message",
    method="DELETE",
    path="/webhooks/{webhook_id}/{webhook_token}/messages/@original",
    input_model=models.DiscordHTTPDeleteOriginalWebhookMessageInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=('thread_id',),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_original_webhook_message": DiscordHTTPOperation(
    id="get_original_webhook_message",
    method="GET",
    path="/webhooks/{webhook_id}/{webhook_token}/messages/@original",
    input_model=models.DiscordHTTPGetOriginalWebhookMessageInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=('thread_id',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_original_webhook_message": DiscordHTTPOperation(
    id="update_original_webhook_message",
    method="PATCH",
    path="/webhooks/{webhook_id}/{webhook_token}/messages/@original",
    input_model=models.DiscordHTTPUpdateOriginalWebhookMessageInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=('thread_id', 'with_components'),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200,),
  ),
  "delete_webhook_message": DiscordHTTPOperation(
    id="delete_webhook_message",
    method="DELETE",
    path="/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}",
    input_model=models.DiscordHTTPDeleteWebhookMessageInput,
    path_fields=('webhook_id', 'webhook_token', 'message_id'),
    query_fields=('thread_id',),
    header_fields=(),
    content_types=(),
    success_statuses=(204,),
  ),
  "get_webhook_message": DiscordHTTPOperation(
    id="get_webhook_message",
    method="GET",
    path="/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}",
    input_model=models.DiscordHTTPGetWebhookMessageInput,
    path_fields=('webhook_id', 'webhook_token', 'message_id'),
    query_fields=('thread_id',),
    header_fields=(),
    content_types=(),
    success_statuses=(200,),
  ),
  "update_webhook_message": DiscordHTTPOperation(
    id="update_webhook_message",
    method="PATCH",
    path="/webhooks/{webhook_id}/{webhook_token}/messages/{message_id}",
    input_model=models.DiscordHTTPUpdateWebhookMessageInput,
    path_fields=('webhook_id', 'webhook_token', 'message_id'),
    query_fields=('thread_id', 'with_components'),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200,),
  ),
  "execute_slack_compatible_webhook": DiscordHTTPOperation(
    id="execute_slack_compatible_webhook",
    method="POST",
    path="/webhooks/{webhook_id}/{webhook_token}/slack",
    input_model=models.DiscordHTTPExecuteSlackCompatibleWebhookInput,
    path_fields=('webhook_id', 'webhook_token'),
    query_fields=('wait', 'thread_id'),
    header_fields=(),
    content_types=(
      'application/json',
      'application/x-www-form-urlencoded',
      'multipart/form-data',
    ),
    success_statuses=(200,),
  ),
}


class GeneratedDiscordHTTPClient[ResponseT]:
  async def _request_operation(
    self, operation: DiscordOperationId, request: BaseModel
  ) -> ResponseT:
    raise NotImplementedError

  async def get_my_application(
    self, request: models.DiscordHTTPGetMyApplicationInput
  ) -> ResponseT:
    return await self._request_operation("get_my_application", request)

  async def update_my_application(
    self, request: models.DiscordHTTPUpdateMyApplicationInput
  ) -> ResponseT:
    return await self._request_operation("update_my_application", request)

  async def get_application(
    self, request: models.DiscordHTTPGetApplicationInput
  ) -> ResponseT:
    return await self._request_operation("get_application", request)

  async def update_application(
    self, request: models.DiscordHTTPUpdateApplicationInput
  ) -> ResponseT:
    return await self._request_operation("update_application", request)

  async def applications_get_activity_instance(
    self, request: models.DiscordHTTPApplicationsGetActivityInstanceInput
  ) -> ResponseT:
    return await self._request_operation("applications_get_activity_instance", request)

  async def upload_application_attachment(
    self, request: models.DiscordHTTPUploadApplicationAttachmentInput
  ) -> ResponseT:
    return await self._request_operation("upload_application_attachment", request)

  async def list_application_commands(
    self, request: models.DiscordHTTPListApplicationCommandsInput
  ) -> ResponseT:
    return await self._request_operation("list_application_commands", request)

  async def create_application_command(
    self, request: models.DiscordHTTPCreateApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("create_application_command", request)

  async def bulk_set_application_commands(
    self, request: models.DiscordHTTPBulkSetApplicationCommandsInput
  ) -> ResponseT:
    return await self._request_operation("bulk_set_application_commands", request)

  async def delete_application_command(
    self, request: models.DiscordHTTPDeleteApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("delete_application_command", request)

  async def get_application_command(
    self, request: models.DiscordHTTPGetApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("get_application_command", request)

  async def update_application_command(
    self, request: models.DiscordHTTPUpdateApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("update_application_command", request)

  async def list_application_emojis(
    self, request: models.DiscordHTTPListApplicationEmojisInput
  ) -> ResponseT:
    return await self._request_operation("list_application_emojis", request)

  async def create_application_emoji(
    self, request: models.DiscordHTTPCreateApplicationEmojiInput
  ) -> ResponseT:
    return await self._request_operation("create_application_emoji", request)

  async def delete_application_emoji(
    self, request: models.DiscordHTTPDeleteApplicationEmojiInput
  ) -> ResponseT:
    return await self._request_operation("delete_application_emoji", request)

  async def get_application_emoji(
    self, request: models.DiscordHTTPGetApplicationEmojiInput
  ) -> ResponseT:
    return await self._request_operation("get_application_emoji", request)

  async def update_application_emoji(
    self, request: models.DiscordHTTPUpdateApplicationEmojiInput
  ) -> ResponseT:
    return await self._request_operation("update_application_emoji", request)

  async def get_entitlements(
    self, request: models.DiscordHTTPGetEntitlementsInput
  ) -> ResponseT:
    return await self._request_operation("get_entitlements", request)

  async def create_entitlement(
    self, request: models.DiscordHTTPCreateEntitlementInput
  ) -> ResponseT:
    return await self._request_operation("create_entitlement", request)

  async def delete_entitlement(
    self, request: models.DiscordHTTPDeleteEntitlementInput
  ) -> ResponseT:
    return await self._request_operation("delete_entitlement", request)

  async def get_entitlement(
    self, request: models.DiscordHTTPGetEntitlementInput
  ) -> ResponseT:
    return await self._request_operation("get_entitlement", request)

  async def consume_entitlement(
    self, request: models.DiscordHTTPConsumeEntitlementInput
  ) -> ResponseT:
    return await self._request_operation("consume_entitlement", request)

  async def list_guild_application_commands(
    self, request: models.DiscordHTTPListGuildApplicationCommandsInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_application_commands", request)

  async def create_guild_application_command(
    self, request: models.DiscordHTTPCreateGuildApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_application_command", request)

  async def bulk_set_guild_application_commands(
    self, request: models.DiscordHTTPBulkSetGuildApplicationCommandsInput
  ) -> ResponseT:
    return await self._request_operation("bulk_set_guild_application_commands", request)

  async def list_guild_application_command_permissions(
    self, request: models.DiscordHTTPListGuildApplicationCommandPermissionsInput
  ) -> ResponseT:
    return await self._request_operation(
      "list_guild_application_command_permissions", request
    )

  async def delete_guild_application_command(
    self, request: models.DiscordHTTPDeleteGuildApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_application_command", request)

  async def get_guild_application_command(
    self, request: models.DiscordHTTPGetGuildApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_application_command", request)

  async def update_guild_application_command(
    self, request: models.DiscordHTTPUpdateGuildApplicationCommandInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_application_command", request)

  async def get_guild_application_command_permissions(
    self, request: models.DiscordHTTPGetGuildApplicationCommandPermissionsInput
  ) -> ResponseT:
    return await self._request_operation(
      "get_guild_application_command_permissions", request
    )

  async def set_guild_application_command_permissions(
    self, request: models.DiscordHTTPSetGuildApplicationCommandPermissionsInput
  ) -> ResponseT:
    return await self._request_operation(
      "set_guild_application_command_permissions", request
    )

  async def get_application_role_connections_metadata(
    self, request: models.DiscordHTTPGetApplicationRoleConnectionsMetadataInput
  ) -> ResponseT:
    return await self._request_operation(
      "get_application_role_connections_metadata", request
    )

  async def update_application_role_connections_metadata(
    self, request: models.DiscordHTTPUpdateApplicationRoleConnectionsMetadataInput
  ) -> ResponseT:
    return await self._request_operation(
      "update_application_role_connections_metadata", request
    )

  async def delete_channel(
    self, request: models.DiscordHTTPDeleteChannelInput
  ) -> ResponseT:
    return await self._request_operation("delete_channel", request)

  async def get_channel(self, request: models.DiscordHTTPGetChannelInput) -> ResponseT:
    return await self._request_operation("get_channel", request)

  async def update_channel(
    self, request: models.DiscordHTTPUpdateChannelInput
  ) -> ResponseT:
    return await self._request_operation("update_channel", request)

  async def follow_channel(
    self, request: models.DiscordHTTPFollowChannelInput
  ) -> ResponseT:
    return await self._request_operation("follow_channel", request)

  async def list_channel_invites(
    self, request: models.DiscordHTTPListChannelInvitesInput
  ) -> ResponseT:
    return await self._request_operation("list_channel_invites", request)

  async def create_channel_invite(
    self, request: models.DiscordHTTPCreateChannelInviteInput
  ) -> ResponseT:
    return await self._request_operation("create_channel_invite", request)

  async def list_messages(
    self, request: models.DiscordHTTPListMessagesInput
  ) -> ResponseT:
    return await self._request_operation("list_messages", request)

  async def create_message(
    self, request: models.DiscordHTTPCreateMessageInput
  ) -> ResponseT:
    return await self._request_operation("create_message", request)

  async def bulk_delete_messages(
    self, request: models.DiscordHTTPBulkDeleteMessagesInput
  ) -> ResponseT:
    return await self._request_operation("bulk_delete_messages", request)

  async def list_pins(self, request: models.DiscordHTTPListPinsInput) -> ResponseT:
    return await self._request_operation("list_pins", request)

  async def delete_pin(self, request: models.DiscordHTTPDeletePinInput) -> ResponseT:
    return await self._request_operation("delete_pin", request)

  async def create_pin(self, request: models.DiscordHTTPCreatePinInput) -> ResponseT:
    return await self._request_operation("create_pin", request)

  async def delete_message(
    self, request: models.DiscordHTTPDeleteMessageInput
  ) -> ResponseT:
    return await self._request_operation("delete_message", request)

  async def get_message(self, request: models.DiscordHTTPGetMessageInput) -> ResponseT:
    return await self._request_operation("get_message", request)

  async def update_message(
    self, request: models.DiscordHTTPUpdateMessageInput
  ) -> ResponseT:
    return await self._request_operation("update_message", request)

  async def crosspost_message(
    self, request: models.DiscordHTTPCrosspostMessageInput
  ) -> ResponseT:
    return await self._request_operation("crosspost_message", request)

  async def delete_all_message_reactions(
    self, request: models.DiscordHTTPDeleteAllMessageReactionsInput
  ) -> ResponseT:
    return await self._request_operation("delete_all_message_reactions", request)

  async def delete_all_message_reactions_by_emoji(
    self, request: models.DiscordHTTPDeleteAllMessageReactionsByEmojiInput
  ) -> ResponseT:
    return await self._request_operation(
      "delete_all_message_reactions_by_emoji", request
    )

  async def list_message_reactions_by_emoji(
    self, request: models.DiscordHTTPListMessageReactionsByEmojiInput
  ) -> ResponseT:
    return await self._request_operation("list_message_reactions_by_emoji", request)

  async def delete_my_message_reaction(
    self, request: models.DiscordHTTPDeleteMyMessageReactionInput
  ) -> ResponseT:
    return await self._request_operation("delete_my_message_reaction", request)

  async def add_my_message_reaction(
    self, request: models.DiscordHTTPAddMyMessageReactionInput
  ) -> ResponseT:
    return await self._request_operation("add_my_message_reaction", request)

  async def delete_user_message_reaction(
    self, request: models.DiscordHTTPDeleteUserMessageReactionInput
  ) -> ResponseT:
    return await self._request_operation("delete_user_message_reaction", request)

  async def create_thread_from_message(
    self, request: models.DiscordHTTPCreateThreadFromMessageInput
  ) -> ResponseT:
    return await self._request_operation("create_thread_from_message", request)

  async def delete_channel_permission_overwrite(
    self, request: models.DiscordHTTPDeleteChannelPermissionOverwriteInput
  ) -> ResponseT:
    return await self._request_operation("delete_channel_permission_overwrite", request)

  async def set_channel_permission_overwrite(
    self, request: models.DiscordHTTPSetChannelPermissionOverwriteInput
  ) -> ResponseT:
    return await self._request_operation("set_channel_permission_overwrite", request)

  async def deprecated_list_pins(
    self, request: models.DiscordHTTPDeprecatedListPinsInput
  ) -> ResponseT:
    return await self._request_operation("deprecated_list_pins", request)

  async def deprecated_delete_pin(
    self, request: models.DiscordHTTPDeprecatedDeletePinInput
  ) -> ResponseT:
    return await self._request_operation("deprecated_delete_pin", request)

  async def deprecated_create_pin(
    self, request: models.DiscordHTTPDeprecatedCreatePinInput
  ) -> ResponseT:
    return await self._request_operation("deprecated_create_pin", request)

  async def get_answer_voters(
    self, request: models.DiscordHTTPGetAnswerVotersInput
  ) -> ResponseT:
    return await self._request_operation("get_answer_voters", request)

  async def poll_expire(self, request: models.DiscordHTTPPollExpireInput) -> ResponseT:
    return await self._request_operation("poll_expire", request)

  async def delete_group_dm_user(
    self, request: models.DiscordHTTPDeleteGroupDmUserInput
  ) -> ResponseT:
    return await self._request_operation("delete_group_dm_user", request)

  async def add_group_dm_user(
    self, request: models.DiscordHTTPAddGroupDmUserInput
  ) -> ResponseT:
    return await self._request_operation("add_group_dm_user", request)

  async def send_soundboard_sound(
    self, request: models.DiscordHTTPSendSoundboardSoundInput
  ) -> ResponseT:
    return await self._request_operation("send_soundboard_sound", request)

  async def list_thread_members(
    self, request: models.DiscordHTTPListThreadMembersInput
  ) -> ResponseT:
    return await self._request_operation("list_thread_members", request)

  async def leave_thread(
    self, request: models.DiscordHTTPLeaveThreadInput
  ) -> ResponseT:
    return await self._request_operation("leave_thread", request)

  async def join_thread(self, request: models.DiscordHTTPJoinThreadInput) -> ResponseT:
    return await self._request_operation("join_thread", request)

  async def delete_thread_member(
    self, request: models.DiscordHTTPDeleteThreadMemberInput
  ) -> ResponseT:
    return await self._request_operation("delete_thread_member", request)

  async def get_thread_member(
    self, request: models.DiscordHTTPGetThreadMemberInput
  ) -> ResponseT:
    return await self._request_operation("get_thread_member", request)

  async def add_thread_member(
    self, request: models.DiscordHTTPAddThreadMemberInput
  ) -> ResponseT:
    return await self._request_operation("add_thread_member", request)

  async def create_thread(
    self, request: models.DiscordHTTPCreateThreadInput
  ) -> ResponseT:
    return await self._request_operation("create_thread", request)

  async def list_private_archived_threads(
    self, request: models.DiscordHTTPListPrivateArchivedThreadsInput
  ) -> ResponseT:
    return await self._request_operation("list_private_archived_threads", request)

  async def list_public_archived_threads(
    self, request: models.DiscordHTTPListPublicArchivedThreadsInput
  ) -> ResponseT:
    return await self._request_operation("list_public_archived_threads", request)

  async def thread_search(
    self, request: models.DiscordHTTPThreadSearchInput
  ) -> ResponseT:
    return await self._request_operation("thread_search", request)

  async def trigger_typing_indicator(
    self, request: models.DiscordHTTPTriggerTypingIndicatorInput
  ) -> ResponseT:
    return await self._request_operation("trigger_typing_indicator", request)

  async def list_my_private_archived_threads(
    self, request: models.DiscordHTTPListMyPrivateArchivedThreadsInput
  ) -> ResponseT:
    return await self._request_operation("list_my_private_archived_threads", request)

  async def update_voice_channel_status(
    self, request: models.DiscordHTTPUpdateVoiceChannelStatusInput
  ) -> ResponseT:
    return await self._request_operation("update_voice_channel_status", request)

  async def list_channel_webhooks(
    self, request: models.DiscordHTTPListChannelWebhooksInput
  ) -> ResponseT:
    return await self._request_operation("list_channel_webhooks", request)

  async def create_webhook(
    self, request: models.DiscordHTTPCreateWebhookInput
  ) -> ResponseT:
    return await self._request_operation("create_webhook", request)

  async def get_gateway(self, request: models.DiscordHTTPGetGatewayInput) -> ResponseT:
    return await self._request_operation("get_gateway", request)

  async def get_bot_gateway(
    self, request: models.DiscordHTTPGetBotGatewayInput
  ) -> ResponseT:
    return await self._request_operation("get_bot_gateway", request)

  async def get_guild_template(
    self, request: models.DiscordHTTPGetGuildTemplateInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_template", request)

  async def get_guild(self, request: models.DiscordHTTPGetGuildInput) -> ResponseT:
    return await self._request_operation("get_guild", request)

  async def update_guild(
    self, request: models.DiscordHTTPUpdateGuildInput
  ) -> ResponseT:
    return await self._request_operation("update_guild", request)

  async def list_guild_audit_log_entries(
    self, request: models.DiscordHTTPListGuildAuditLogEntriesInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_audit_log_entries", request)

  async def list_auto_moderation_rules(
    self, request: models.DiscordHTTPListAutoModerationRulesInput
  ) -> ResponseT:
    return await self._request_operation("list_auto_moderation_rules", request)

  async def create_auto_moderation_rule(
    self, request: models.DiscordHTTPCreateAutoModerationRuleInput
  ) -> ResponseT:
    return await self._request_operation("create_auto_moderation_rule", request)

  async def delete_auto_moderation_rule(
    self, request: models.DiscordHTTPDeleteAutoModerationRuleInput
  ) -> ResponseT:
    return await self._request_operation("delete_auto_moderation_rule", request)

  async def get_auto_moderation_rule(
    self, request: models.DiscordHTTPGetAutoModerationRuleInput
  ) -> ResponseT:
    return await self._request_operation("get_auto_moderation_rule", request)

  async def update_auto_moderation_rule(
    self, request: models.DiscordHTTPUpdateAutoModerationRuleInput
  ) -> ResponseT:
    return await self._request_operation("update_auto_moderation_rule", request)

  async def list_guild_bans(
    self, request: models.DiscordHTTPListGuildBansInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_bans", request)

  async def unban_user_from_guild(
    self, request: models.DiscordHTTPUnbanUserFromGuildInput
  ) -> ResponseT:
    return await self._request_operation("unban_user_from_guild", request)

  async def get_guild_ban(
    self, request: models.DiscordHTTPGetGuildBanInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_ban", request)

  async def ban_user_from_guild(
    self, request: models.DiscordHTTPBanUserFromGuildInput
  ) -> ResponseT:
    return await self._request_operation("ban_user_from_guild", request)

  async def bulk_ban_users_from_guild(
    self, request: models.DiscordHTTPBulkBanUsersFromGuildInput
  ) -> ResponseT:
    return await self._request_operation("bulk_ban_users_from_guild", request)

  async def list_guild_channels(
    self, request: models.DiscordHTTPListGuildChannelsInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_channels", request)

  async def bulk_update_guild_channels(
    self, request: models.DiscordHTTPBulkUpdateGuildChannelsInput
  ) -> ResponseT:
    return await self._request_operation("bulk_update_guild_channels", request)

  async def create_guild_channel(
    self, request: models.DiscordHTTPCreateGuildChannelInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_channel", request)

  async def list_guild_emojis(
    self, request: models.DiscordHTTPListGuildEmojisInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_emojis", request)

  async def create_guild_emoji(
    self, request: models.DiscordHTTPCreateGuildEmojiInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_emoji", request)

  async def delete_guild_emoji(
    self, request: models.DiscordHTTPDeleteGuildEmojiInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_emoji", request)

  async def get_guild_emoji(
    self, request: models.DiscordHTTPGetGuildEmojiInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_emoji", request)

  async def update_guild_emoji(
    self, request: models.DiscordHTTPUpdateGuildEmojiInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_emoji", request)

  async def update_guild_incident_actions(
    self, request: models.DiscordHTTPUpdateGuildIncidentActionsInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_incident_actions", request)

  async def list_guild_integrations(
    self, request: models.DiscordHTTPListGuildIntegrationsInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_integrations", request)

  async def delete_guild_integration(
    self, request: models.DiscordHTTPDeleteGuildIntegrationInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_integration", request)

  async def list_guild_invites(
    self, request: models.DiscordHTTPListGuildInvitesInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_invites", request)

  async def list_guild_members(
    self, request: models.DiscordHTTPListGuildMembersInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_members", request)

  async def update_my_guild_member(
    self, request: models.DiscordHTTPUpdateMyGuildMemberInput
  ) -> ResponseT:
    return await self._request_operation("update_my_guild_member", request)

  async def search_guild_members(
    self, request: models.DiscordHTTPSearchGuildMembersInput
  ) -> ResponseT:
    return await self._request_operation("search_guild_members", request)

  async def delete_guild_member(
    self, request: models.DiscordHTTPDeleteGuildMemberInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_member", request)

  async def get_guild_member(
    self, request: models.DiscordHTTPGetGuildMemberInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_member", request)

  async def update_guild_member(
    self, request: models.DiscordHTTPUpdateGuildMemberInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_member", request)

  async def add_guild_member(
    self, request: models.DiscordHTTPAddGuildMemberInput
  ) -> ResponseT:
    return await self._request_operation("add_guild_member", request)

  async def delete_guild_member_role(
    self, request: models.DiscordHTTPDeleteGuildMemberRoleInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_member_role", request)

  async def add_guild_member_role(
    self, request: models.DiscordHTTPAddGuildMemberRoleInput
  ) -> ResponseT:
    return await self._request_operation("add_guild_member_role", request)

  async def guild_search(
    self, request: models.DiscordHTTPGuildSearchInput
  ) -> ResponseT:
    return await self._request_operation("guild_search", request)

  async def get_guild_new_member_welcome(
    self, request: models.DiscordHTTPGetGuildNewMemberWelcomeInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_new_member_welcome", request)

  async def get_guilds_onboarding(
    self, request: models.DiscordHTTPGetGuildsOnboardingInput
  ) -> ResponseT:
    return await self._request_operation("get_guilds_onboarding", request)

  async def put_guilds_onboarding(
    self, request: models.DiscordHTTPPutGuildsOnboardingInput
  ) -> ResponseT:
    return await self._request_operation("put_guilds_onboarding", request)

  async def get_guild_preview(
    self, request: models.DiscordHTTPGetGuildPreviewInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_preview", request)

  async def preview_prune_guild(
    self, request: models.DiscordHTTPPreviewPruneGuildInput
  ) -> ResponseT:
    return await self._request_operation("preview_prune_guild", request)

  async def prune_guild(self, request: models.DiscordHTTPPruneGuildInput) -> ResponseT:
    return await self._request_operation("prune_guild", request)

  async def list_guild_voice_regions(
    self, request: models.DiscordHTTPListGuildVoiceRegionsInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_voice_regions", request)

  async def get_guild_join_requests(
    self, request: models.DiscordHTTPGetGuildJoinRequestsInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_join_requests", request)

  async def action_guild_join_request(
    self, request: models.DiscordHTTPActionGuildJoinRequestInput
  ) -> ResponseT:
    return await self._request_operation("action_guild_join_request", request)

  async def list_guild_roles(
    self, request: models.DiscordHTTPListGuildRolesInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_roles", request)

  async def bulk_update_guild_roles(
    self, request: models.DiscordHTTPBulkUpdateGuildRolesInput
  ) -> ResponseT:
    return await self._request_operation("bulk_update_guild_roles", request)

  async def create_guild_role(
    self, request: models.DiscordHTTPCreateGuildRoleInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_role", request)

  async def guild_role_member_counts(
    self, request: models.DiscordHTTPGuildRoleMemberCountsInput
  ) -> ResponseT:
    return await self._request_operation("guild_role_member_counts", request)

  async def delete_guild_role(
    self, request: models.DiscordHTTPDeleteGuildRoleInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_role", request)

  async def get_guild_role(
    self, request: models.DiscordHTTPGetGuildRoleInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_role", request)

  async def update_guild_role(
    self, request: models.DiscordHTTPUpdateGuildRoleInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_role", request)

  async def list_guild_scheduled_events(
    self, request: models.DiscordHTTPListGuildScheduledEventsInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_scheduled_events", request)

  async def create_guild_scheduled_event(
    self, request: models.DiscordHTTPCreateGuildScheduledEventInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_scheduled_event", request)

  async def delete_guild_scheduled_event(
    self, request: models.DiscordHTTPDeleteGuildScheduledEventInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_scheduled_event", request)

  async def get_guild_scheduled_event(
    self, request: models.DiscordHTTPGetGuildScheduledEventInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_scheduled_event", request)

  async def update_guild_scheduled_event(
    self, request: models.DiscordHTTPUpdateGuildScheduledEventInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_scheduled_event", request)

  async def create_guild_scheduled_event_exception(
    self, request: models.DiscordHTTPCreateGuildScheduledEventExceptionInput
  ) -> ResponseT:
    return await self._request_operation(
      "create_guild_scheduled_event_exception", request
    )

  async def delete_guild_scheduled_event_exception(
    self, request: models.DiscordHTTPDeleteGuildScheduledEventExceptionInput
  ) -> ResponseT:
    return await self._request_operation(
      "delete_guild_scheduled_event_exception", request
    )

  async def update_guild_scheduled_event_exception(
    self, request: models.DiscordHTTPUpdateGuildScheduledEventExceptionInput
  ) -> ResponseT:
    return await self._request_operation(
      "update_guild_scheduled_event_exception", request
    )

  async def list_guild_scheduled_event_users(
    self, request: models.DiscordHTTPListGuildScheduledEventUsersInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_scheduled_event_users", request)

  async def count_guild_scheduled_event_users(
    self, request: models.DiscordHTTPCountGuildScheduledEventUsersInput
  ) -> ResponseT:
    return await self._request_operation("count_guild_scheduled_event_users", request)

  async def list_guild_scheduled_event_exception_users(
    self, request: models.DiscordHTTPListGuildScheduledEventExceptionUsersInput
  ) -> ResponseT:
    return await self._request_operation(
      "list_guild_scheduled_event_exception_users", request
    )

  async def list_guild_soundboard_sounds(
    self, request: models.DiscordHTTPListGuildSoundboardSoundsInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_soundboard_sounds", request)

  async def create_guild_soundboard_sound(
    self, request: models.DiscordHTTPCreateGuildSoundboardSoundInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_soundboard_sound", request)

  async def delete_guild_soundboard_sound(
    self, request: models.DiscordHTTPDeleteGuildSoundboardSoundInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_soundboard_sound", request)

  async def get_guild_soundboard_sound(
    self, request: models.DiscordHTTPGetGuildSoundboardSoundInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_soundboard_sound", request)

  async def update_guild_soundboard_sound(
    self, request: models.DiscordHTTPUpdateGuildSoundboardSoundInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_soundboard_sound", request)

  async def list_guild_stickers(
    self, request: models.DiscordHTTPListGuildStickersInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_stickers", request)

  async def create_guild_sticker(
    self, request: models.DiscordHTTPCreateGuildStickerInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_sticker", request)

  async def delete_guild_sticker(
    self, request: models.DiscordHTTPDeleteGuildStickerInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_sticker", request)

  async def get_guild_sticker(
    self, request: models.DiscordHTTPGetGuildStickerInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_sticker", request)

  async def update_guild_sticker(
    self, request: models.DiscordHTTPUpdateGuildStickerInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_sticker", request)

  async def list_guild_templates(
    self, request: models.DiscordHTTPListGuildTemplatesInput
  ) -> ResponseT:
    return await self._request_operation("list_guild_templates", request)

  async def create_guild_template(
    self, request: models.DiscordHTTPCreateGuildTemplateInput
  ) -> ResponseT:
    return await self._request_operation("create_guild_template", request)

  async def delete_guild_template(
    self, request: models.DiscordHTTPDeleteGuildTemplateInput
  ) -> ResponseT:
    return await self._request_operation("delete_guild_template", request)

  async def update_guild_template(
    self, request: models.DiscordHTTPUpdateGuildTemplateInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_template", request)

  async def sync_guild_template(
    self, request: models.DiscordHTTPSyncGuildTemplateInput
  ) -> ResponseT:
    return await self._request_operation("sync_guild_template", request)

  async def get_active_guild_threads(
    self, request: models.DiscordHTTPGetActiveGuildThreadsInput
  ) -> ResponseT:
    return await self._request_operation("get_active_guild_threads", request)

  async def get_guild_vanity_url(
    self, request: models.DiscordHTTPGetGuildVanityUrlInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_vanity_url", request)

  async def get_self_voice_state(
    self, request: models.DiscordHTTPGetSelfVoiceStateInput
  ) -> ResponseT:
    return await self._request_operation("get_self_voice_state", request)

  async def update_self_voice_state(
    self, request: models.DiscordHTTPUpdateSelfVoiceStateInput
  ) -> ResponseT:
    return await self._request_operation("update_self_voice_state", request)

  async def get_voice_state(
    self, request: models.DiscordHTTPGetVoiceStateInput
  ) -> ResponseT:
    return await self._request_operation("get_voice_state", request)

  async def update_voice_state(
    self, request: models.DiscordHTTPUpdateVoiceStateInput
  ) -> ResponseT:
    return await self._request_operation("update_voice_state", request)

  async def get_guild_webhooks(
    self, request: models.DiscordHTTPGetGuildWebhooksInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_webhooks", request)

  async def get_guild_welcome_screen(
    self, request: models.DiscordHTTPGetGuildWelcomeScreenInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_welcome_screen", request)

  async def update_guild_welcome_screen(
    self, request: models.DiscordHTTPUpdateGuildWelcomeScreenInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_welcome_screen", request)

  async def get_guild_widget_settings(
    self, request: models.DiscordHTTPGetGuildWidgetSettingsInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_widget_settings", request)

  async def update_guild_widget_settings(
    self, request: models.DiscordHTTPUpdateGuildWidgetSettingsInput
  ) -> ResponseT:
    return await self._request_operation("update_guild_widget_settings", request)

  async def get_guild_widget(
    self, request: models.DiscordHTTPGetGuildWidgetInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_widget", request)

  async def get_guild_widget_png(
    self, request: models.DiscordHTTPGetGuildWidgetPngInput
  ) -> ResponseT:
    return await self._request_operation("get_guild_widget_png", request)

  async def create_interaction_response(
    self, request: models.DiscordHTTPCreateInteractionResponseInput
  ) -> ResponseT:
    return await self._request_operation("create_interaction_response", request)

  async def invite_revoke(
    self, request: models.DiscordHTTPInviteRevokeInput
  ) -> ResponseT:
    return await self._request_operation("invite_revoke", request)

  async def invite_resolve(
    self, request: models.DiscordHTTPInviteResolveInput
  ) -> ResponseT:
    return await self._request_operation("invite_resolve", request)

  async def get_invite_target_users(
    self, request: models.DiscordHTTPGetInviteTargetUsersInput
  ) -> ResponseT:
    return await self._request_operation("get_invite_target_users", request)

  async def update_invite_target_users(
    self, request: models.DiscordHTTPUpdateInviteTargetUsersInput
  ) -> ResponseT:
    return await self._request_operation("update_invite_target_users", request)

  async def get_invite_target_users_job_status(
    self, request: models.DiscordHTTPGetInviteTargetUsersJobStatusInput
  ) -> ResponseT:
    return await self._request_operation("get_invite_target_users_job_status", request)

  async def create_lobby(
    self, request: models.DiscordHTTPCreateLobbyInput
  ) -> ResponseT:
    return await self._request_operation("create_lobby", request)

  async def create_or_join_lobby(
    self, request: models.DiscordHTTPCreateOrJoinLobbyInput
  ) -> ResponseT:
    return await self._request_operation("create_or_join_lobby", request)

  async def delete_lobby(
    self, request: models.DiscordHTTPDeleteLobbyInput
  ) -> ResponseT:
    return await self._request_operation("delete_lobby", request)

  async def get_lobby(self, request: models.DiscordHTTPGetLobbyInput) -> ResponseT:
    return await self._request_operation("get_lobby", request)

  async def edit_lobby(self, request: models.DiscordHTTPEditLobbyInput) -> ResponseT:
    return await self._request_operation("edit_lobby", request)

  async def edit_lobby_channel_link(
    self, request: models.DiscordHTTPEditLobbyChannelLinkInput
  ) -> ResponseT:
    return await self._request_operation("edit_lobby_channel_link", request)

  async def leave_lobby(self, request: models.DiscordHTTPLeaveLobbyInput) -> ResponseT:
    return await self._request_operation("leave_lobby", request)

  async def create_linked_lobby_guild_invite_for_self(
    self, request: models.DiscordHTTPCreateLinkedLobbyGuildInviteForSelfInput
  ) -> ResponseT:
    return await self._request_operation(
      "create_linked_lobby_guild_invite_for_self", request
    )

  async def bulk_update_lobby_members(
    self, request: models.DiscordHTTPBulkUpdateLobbyMembersInput
  ) -> ResponseT:
    return await self._request_operation("bulk_update_lobby_members", request)

  async def delete_lobby_member(
    self, request: models.DiscordHTTPDeleteLobbyMemberInput
  ) -> ResponseT:
    return await self._request_operation("delete_lobby_member", request)

  async def add_lobby_member(
    self, request: models.DiscordHTTPAddLobbyMemberInput
  ) -> ResponseT:
    return await self._request_operation("add_lobby_member", request)

  async def create_linked_lobby_guild_invite_for_user(
    self, request: models.DiscordHTTPCreateLinkedLobbyGuildInviteForUserInput
  ) -> ResponseT:
    return await self._request_operation(
      "create_linked_lobby_guild_invite_for_user", request
    )

  async def get_lobby_messages(
    self, request: models.DiscordHTTPGetLobbyMessagesInput
  ) -> ResponseT:
    return await self._request_operation("get_lobby_messages", request)

  async def create_lobby_message(
    self, request: models.DiscordHTTPCreateLobbyMessageInput
  ) -> ResponseT:
    return await self._request_operation("create_lobby_message", request)

  async def update_lobby_message_external_moderation_metadata(
    self, request: models.DiscordHTTPUpdateLobbyMessageExternalModerationMetadataInput
  ) -> ResponseT:
    return await self._request_operation(
      "update_lobby_message_external_moderation_metadata", request
    )

  async def get_my_oauth2_authorization(
    self, request: models.DiscordHTTPGetMyOauth2AuthorizationInput
  ) -> ResponseT:
    return await self._request_operation("get_my_oauth2_authorization", request)

  async def get_my_oauth2_application(
    self, request: models.DiscordHTTPGetMyOauth2ApplicationInput
  ) -> ResponseT:
    return await self._request_operation("get_my_oauth2_application", request)

  async def get_public_keys(
    self, request: models.DiscordHTTPGetPublicKeysInput
  ) -> ResponseT:
    return await self._request_operation("get_public_keys", request)

  async def get_openid_connect_userinfo(
    self, request: models.DiscordHTTPGetOpenidConnectUserinfoInput
  ) -> ResponseT:
    return await self._request_operation("get_openid_connect_userinfo", request)

  async def update_user_message_external_moderation_metadata(
    self, request: models.DiscordHTTPUpdateUserMessageExternalModerationMetadataInput
  ) -> ResponseT:
    return await self._request_operation(
      "update_user_message_external_moderation_metadata", request
    )

  async def partner_sdk_unmerge_provisional_account(
    self, request: models.DiscordHTTPPartnerSdkUnmergeProvisionalAccountInput
  ) -> ResponseT:
    return await self._request_operation(
      "partner_sdk_unmerge_provisional_account", request
    )

  async def bot_partner_sdk_unmerge_provisional_account(
    self, request: models.DiscordHTTPBotPartnerSdkUnmergeProvisionalAccountInput
  ) -> ResponseT:
    return await self._request_operation(
      "bot_partner_sdk_unmerge_provisional_account", request
    )

  async def partner_sdk_token(
    self, request: models.DiscordHTTPPartnerSdkTokenInput
  ) -> ResponseT:
    return await self._request_operation("partner_sdk_token", request)

  async def bot_partner_sdk_token(
    self, request: models.DiscordHTTPBotPartnerSdkTokenInput
  ) -> ResponseT:
    return await self._request_operation("bot_partner_sdk_token", request)

  async def get_sku_subscriptions(
    self, request: models.DiscordHTTPGetSkuSubscriptionsInput
  ) -> ResponseT:
    return await self._request_operation("get_sku_subscriptions", request)

  async def get_sku_subscription(
    self, request: models.DiscordHTTPGetSkuSubscriptionInput
  ) -> ResponseT:
    return await self._request_operation("get_sku_subscription", request)

  async def get_soundboard_default_sounds(
    self, request: models.DiscordHTTPGetSoundboardDefaultSoundsInput
  ) -> ResponseT:
    return await self._request_operation("get_soundboard_default_sounds", request)

  async def create_stage_instance(
    self, request: models.DiscordHTTPCreateStageInstanceInput
  ) -> ResponseT:
    return await self._request_operation("create_stage_instance", request)

  async def delete_stage_instance(
    self, request: models.DiscordHTTPDeleteStageInstanceInput
  ) -> ResponseT:
    return await self._request_operation("delete_stage_instance", request)

  async def get_stage_instance(
    self, request: models.DiscordHTTPGetStageInstanceInput
  ) -> ResponseT:
    return await self._request_operation("get_stage_instance", request)

  async def update_stage_instance(
    self, request: models.DiscordHTTPUpdateStageInstanceInput
  ) -> ResponseT:
    return await self._request_operation("update_stage_instance", request)

  async def list_sticker_packs(
    self, request: models.DiscordHTTPListStickerPacksInput
  ) -> ResponseT:
    return await self._request_operation("list_sticker_packs", request)

  async def get_sticker_pack(
    self, request: models.DiscordHTTPGetStickerPackInput
  ) -> ResponseT:
    return await self._request_operation("get_sticker_pack", request)

  async def get_sticker(self, request: models.DiscordHTTPGetStickerInput) -> ResponseT:
    return await self._request_operation("get_sticker", request)

  async def get_my_user(self, request: models.DiscordHTTPGetMyUserInput) -> ResponseT:
    return await self._request_operation("get_my_user", request)

  async def update_my_user(
    self, request: models.DiscordHTTPUpdateMyUserInput
  ) -> ResponseT:
    return await self._request_operation("update_my_user", request)

  async def get_current_user_application_entitlements(
    self, request: models.DiscordHTTPGetCurrentUserApplicationEntitlementsInput
  ) -> ResponseT:
    return await self._request_operation(
      "get_current_user_application_entitlements", request
    )

  async def delete_application_user_role_connection(
    self, request: models.DiscordHTTPDeleteApplicationUserRoleConnectionInput
  ) -> ResponseT:
    return await self._request_operation(
      "delete_application_user_role_connection", request
    )

  async def get_application_user_role_connection(
    self, request: models.DiscordHTTPGetApplicationUserRoleConnectionInput
  ) -> ResponseT:
    return await self._request_operation(
      "get_application_user_role_connection", request
    )

  async def update_application_user_role_connection(
    self, request: models.DiscordHTTPUpdateApplicationUserRoleConnectionInput
  ) -> ResponseT:
    return await self._request_operation(
      "update_application_user_role_connection", request
    )

  async def create_dm(self, request: models.DiscordHTTPCreateDmInput) -> ResponseT:
    return await self._request_operation("create_dm", request)

  async def list_my_connections(
    self, request: models.DiscordHTTPListMyConnectionsInput
  ) -> ResponseT:
    return await self._request_operation("list_my_connections", request)

  async def list_my_guilds(
    self, request: models.DiscordHTTPListMyGuildsInput
  ) -> ResponseT:
    return await self._request_operation("list_my_guilds", request)

  async def leave_guild(self, request: models.DiscordHTTPLeaveGuildInput) -> ResponseT:
    return await self._request_operation("leave_guild", request)

  async def get_my_guild_member(
    self, request: models.DiscordHTTPGetMyGuildMemberInput
  ) -> ResponseT:
    return await self._request_operation("get_my_guild_member", request)

  async def get_user(self, request: models.DiscordHTTPGetUserInput) -> ResponseT:
    return await self._request_operation("get_user", request)

  async def list_voice_regions(
    self, request: models.DiscordHTTPListVoiceRegionsInput
  ) -> ResponseT:
    return await self._request_operation("list_voice_regions", request)

  async def delete_webhook(
    self, request: models.DiscordHTTPDeleteWebhookInput
  ) -> ResponseT:
    return await self._request_operation("delete_webhook", request)

  async def get_webhook(self, request: models.DiscordHTTPGetWebhookInput) -> ResponseT:
    return await self._request_operation("get_webhook", request)

  async def update_webhook(
    self, request: models.DiscordHTTPUpdateWebhookInput
  ) -> ResponseT:
    return await self._request_operation("update_webhook", request)

  async def delete_webhook_by_token(
    self, request: models.DiscordHTTPDeleteWebhookByTokenInput
  ) -> ResponseT:
    return await self._request_operation("delete_webhook_by_token", request)

  async def get_webhook_by_token(
    self, request: models.DiscordHTTPGetWebhookByTokenInput
  ) -> ResponseT:
    return await self._request_operation("get_webhook_by_token", request)

  async def update_webhook_by_token(
    self, request: models.DiscordHTTPUpdateWebhookByTokenInput
  ) -> ResponseT:
    return await self._request_operation("update_webhook_by_token", request)

  async def execute_webhook(
    self, request: models.DiscordHTTPExecuteWebhookInput
  ) -> ResponseT:
    return await self._request_operation("execute_webhook", request)

  async def execute_github_compatible_webhook(
    self, request: models.DiscordHTTPExecuteGithubCompatibleWebhookInput
  ) -> ResponseT:
    return await self._request_operation("execute_github_compatible_webhook", request)

  async def delete_original_webhook_message(
    self, request: models.DiscordHTTPDeleteOriginalWebhookMessageInput
  ) -> ResponseT:
    return await self._request_operation("delete_original_webhook_message", request)

  async def get_original_webhook_message(
    self, request: models.DiscordHTTPGetOriginalWebhookMessageInput
  ) -> ResponseT:
    return await self._request_operation("get_original_webhook_message", request)

  async def update_original_webhook_message(
    self, request: models.DiscordHTTPUpdateOriginalWebhookMessageInput
  ) -> ResponseT:
    return await self._request_operation("update_original_webhook_message", request)

  async def delete_webhook_message(
    self, request: models.DiscordHTTPDeleteWebhookMessageInput
  ) -> ResponseT:
    return await self._request_operation("delete_webhook_message", request)

  async def get_webhook_message(
    self, request: models.DiscordHTTPGetWebhookMessageInput
  ) -> ResponseT:
    return await self._request_operation("get_webhook_message", request)

  async def update_webhook_message(
    self, request: models.DiscordHTTPUpdateWebhookMessageInput
  ) -> ResponseT:
    return await self._request_operation("update_webhook_message", request)

  async def execute_slack_compatible_webhook(
    self, request: models.DiscordHTTPExecuteSlackCompatibleWebhookInput
  ) -> ResponseT:
    return await self._request_operation("execute_slack_compatible_webhook", request)


__all__ = (
  "HTTP_OPERATIONS",
  "DiscordHTTPOperation",
  "DiscordOperationId",
  "GeneratedDiscordHTTPClient",
)
