# Generated from Discord's OpenAPI specification. Do not edit directly.

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, RootModel

from .models import http_requests as requests

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
  request_model: type[BaseModel]
  response_model: type[BaseModel]
  response_body_model: type[RootModel]
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
    request_model=requests.GetMyApplicationHTTPRequest,
    response_model=requests.GetMyApplicationHTTPResponse,
    response_body_model=requests.GetMyApplicationHTTPResponseBody,
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
    request_model=requests.UpdateMyApplicationHTTPRequest,
    response_model=requests.UpdateMyApplicationHTTPResponse,
    response_body_model=requests.UpdateMyApplicationHTTPResponseBody,
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
    request_model=requests.GetApplicationHTTPRequest,
    response_model=requests.GetApplicationHTTPResponse,
    response_body_model=requests.GetApplicationHTTPResponseBody,
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
    request_model=requests.UpdateApplicationHTTPRequest,
    response_model=requests.UpdateApplicationHTTPResponse,
    response_body_model=requests.UpdateApplicationHTTPResponseBody,
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
    request_model=requests.ApplicationsGetActivityInstanceHTTPRequest,
    response_model=requests.ApplicationsGetActivityInstanceHTTPResponse,
    response_body_model=requests.ApplicationsGetActivityInstanceHTTPResponseBody,
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
    request_model=requests.UploadApplicationAttachmentHTTPRequest,
    response_model=requests.UploadApplicationAttachmentHTTPResponse,
    response_body_model=requests.UploadApplicationAttachmentHTTPResponseBody,
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
    request_model=requests.ListApplicationCommandsHTTPRequest,
    response_model=requests.ListApplicationCommandsHTTPResponse,
    response_body_model=requests.ListApplicationCommandsHTTPResponseBody,
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
    request_model=requests.CreateApplicationCommandHTTPRequest,
    response_model=requests.CreateApplicationCommandHTTPResponse,
    response_body_model=requests.CreateApplicationCommandHTTPResponseBody,
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
    request_model=requests.BulkSetApplicationCommandsHTTPRequest,
    response_model=requests.BulkSetApplicationCommandsHTTPResponse,
    response_body_model=requests.BulkSetApplicationCommandsHTTPResponseBody,
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
    request_model=requests.DeleteApplicationCommandHTTPRequest,
    response_model=requests.DeleteApplicationCommandHTTPResponse,
    response_body_model=requests.DeleteApplicationCommandHTTPResponseBody,
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
    request_model=requests.GetApplicationCommandHTTPRequest,
    response_model=requests.GetApplicationCommandHTTPResponse,
    response_body_model=requests.GetApplicationCommandHTTPResponseBody,
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
    request_model=requests.UpdateApplicationCommandHTTPRequest,
    response_model=requests.UpdateApplicationCommandHTTPResponse,
    response_body_model=requests.UpdateApplicationCommandHTTPResponseBody,
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
    request_model=requests.ListApplicationEmojisHTTPRequest,
    response_model=requests.ListApplicationEmojisHTTPResponse,
    response_body_model=requests.ListApplicationEmojisHTTPResponseBody,
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
    request_model=requests.CreateApplicationEmojiHTTPRequest,
    response_model=requests.CreateApplicationEmojiHTTPResponse,
    response_body_model=requests.CreateApplicationEmojiHTTPResponseBody,
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
    request_model=requests.DeleteApplicationEmojiHTTPRequest,
    response_model=requests.DeleteApplicationEmojiHTTPResponse,
    response_body_model=requests.DeleteApplicationEmojiHTTPResponseBody,
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
    request_model=requests.GetApplicationEmojiHTTPRequest,
    response_model=requests.GetApplicationEmojiHTTPResponse,
    response_body_model=requests.GetApplicationEmojiHTTPResponseBody,
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
    request_model=requests.UpdateApplicationEmojiHTTPRequest,
    response_model=requests.UpdateApplicationEmojiHTTPResponse,
    response_body_model=requests.UpdateApplicationEmojiHTTPResponseBody,
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
    request_model=requests.GetEntitlementsHTTPRequest,
    response_model=requests.GetEntitlementsHTTPResponse,
    response_body_model=requests.GetEntitlementsHTTPResponseBody,
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
    request_model=requests.CreateEntitlementHTTPRequest,
    response_model=requests.CreateEntitlementHTTPResponse,
    response_body_model=requests.CreateEntitlementHTTPResponseBody,
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
    request_model=requests.DeleteEntitlementHTTPRequest,
    response_model=requests.DeleteEntitlementHTTPResponse,
    response_body_model=requests.DeleteEntitlementHTTPResponseBody,
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
    request_model=requests.GetEntitlementHTTPRequest,
    response_model=requests.GetEntitlementHTTPResponse,
    response_body_model=requests.GetEntitlementHTTPResponseBody,
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
    request_model=requests.ConsumeEntitlementHTTPRequest,
    response_model=requests.ConsumeEntitlementHTTPResponse,
    response_body_model=requests.ConsumeEntitlementHTTPResponseBody,
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
    request_model=requests.ListGuildApplicationCommandsHTTPRequest,
    response_model=requests.ListGuildApplicationCommandsHTTPResponse,
    response_body_model=requests.ListGuildApplicationCommandsHTTPResponseBody,
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
    request_model=requests.CreateGuildApplicationCommandHTTPRequest,
    response_model=requests.CreateGuildApplicationCommandHTTPResponse,
    response_body_model=requests.CreateGuildApplicationCommandHTTPResponseBody,
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
    request_model=requests.BulkSetGuildApplicationCommandsHTTPRequest,
    response_model=requests.BulkSetGuildApplicationCommandsHTTPResponse,
    response_body_model=requests.BulkSetGuildApplicationCommandsHTTPResponseBody,
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
    request_model=requests.ListGuildApplicationCommandPermissionsHTTPRequest,
    response_model=requests.ListGuildApplicationCommandPermissionsHTTPResponse,
    response_body_model=requests.ListGuildApplicationCommandPermissionsHTTPResponseBody,
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
    request_model=requests.DeleteGuildApplicationCommandHTTPRequest,
    response_model=requests.DeleteGuildApplicationCommandHTTPResponse,
    response_body_model=requests.DeleteGuildApplicationCommandHTTPResponseBody,
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
    request_model=requests.GetGuildApplicationCommandHTTPRequest,
    response_model=requests.GetGuildApplicationCommandHTTPResponse,
    response_body_model=requests.GetGuildApplicationCommandHTTPResponseBody,
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
    request_model=requests.UpdateGuildApplicationCommandHTTPRequest,
    response_model=requests.UpdateGuildApplicationCommandHTTPResponse,
    response_body_model=requests.UpdateGuildApplicationCommandHTTPResponseBody,
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
    request_model=requests.GetGuildApplicationCommandPermissionsHTTPRequest,
    response_model=requests.GetGuildApplicationCommandPermissionsHTTPResponse,
    response_body_model=requests.GetGuildApplicationCommandPermissionsHTTPResponseBody,
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
    request_model=requests.SetGuildApplicationCommandPermissionsHTTPRequest,
    response_model=requests.SetGuildApplicationCommandPermissionsHTTPResponse,
    response_body_model=requests.SetGuildApplicationCommandPermissionsHTTPResponseBody,
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
    request_model=requests.GetApplicationRoleConnectionsMetadataHTTPRequest,
    response_model=requests.GetApplicationRoleConnectionsMetadataHTTPResponse,
    response_body_model=requests.GetApplicationRoleConnectionsMetadataHTTPResponseBody,
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
    request_model=requests.UpdateApplicationRoleConnectionsMetadataHTTPRequest,
    response_model=requests.UpdateApplicationRoleConnectionsMetadataHTTPResponse,
    response_body_model=requests.UpdateApplicationRoleConnectionsMetadataHTTPResponseBody,
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
    request_model=requests.DeleteChannelHTTPRequest,
    response_model=requests.DeleteChannelHTTPResponse,
    response_body_model=requests.DeleteChannelHTTPResponseBody,
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
    request_model=requests.GetChannelHTTPRequest,
    response_model=requests.GetChannelHTTPResponse,
    response_body_model=requests.GetChannelHTTPResponseBody,
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
    request_model=requests.UpdateChannelHTTPRequest,
    response_model=requests.UpdateChannelHTTPResponse,
    response_body_model=requests.UpdateChannelHTTPResponseBody,
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
    request_model=requests.FollowChannelHTTPRequest,
    response_model=requests.FollowChannelHTTPResponse,
    response_body_model=requests.FollowChannelHTTPResponseBody,
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
    request_model=requests.ListChannelInvitesHTTPRequest,
    response_model=requests.ListChannelInvitesHTTPResponse,
    response_body_model=requests.ListChannelInvitesHTTPResponseBody,
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
    request_model=requests.CreateChannelInviteHTTPRequest,
    response_model=requests.CreateChannelInviteHTTPResponse,
    response_body_model=requests.CreateChannelInviteHTTPResponseBody,
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
    request_model=requests.ListMessagesHTTPRequest,
    response_model=requests.ListMessagesHTTPResponse,
    response_body_model=requests.ListMessagesHTTPResponseBody,
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
    request_model=requests.CreateMessageHTTPRequest,
    response_model=requests.CreateMessageHTTPResponse,
    response_body_model=requests.CreateMessageHTTPResponseBody,
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
    request_model=requests.BulkDeleteMessagesHTTPRequest,
    response_model=requests.BulkDeleteMessagesHTTPResponse,
    response_body_model=requests.BulkDeleteMessagesHTTPResponseBody,
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
    request_model=requests.ListPinsHTTPRequest,
    response_model=requests.ListPinsHTTPResponse,
    response_body_model=requests.ListPinsHTTPResponseBody,
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
    request_model=requests.DeletePinHTTPRequest,
    response_model=requests.DeletePinHTTPResponse,
    response_body_model=requests.DeletePinHTTPResponseBody,
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
    request_model=requests.CreatePinHTTPRequest,
    response_model=requests.CreatePinHTTPResponse,
    response_body_model=requests.CreatePinHTTPResponseBody,
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
    request_model=requests.DeleteMessageHTTPRequest,
    response_model=requests.DeleteMessageHTTPResponse,
    response_body_model=requests.DeleteMessageHTTPResponseBody,
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
    request_model=requests.GetMessageHTTPRequest,
    response_model=requests.GetMessageHTTPResponse,
    response_body_model=requests.GetMessageHTTPResponseBody,
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
    request_model=requests.UpdateMessageHTTPRequest,
    response_model=requests.UpdateMessageHTTPResponse,
    response_body_model=requests.UpdateMessageHTTPResponseBody,
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
    request_model=requests.CrosspostMessageHTTPRequest,
    response_model=requests.CrosspostMessageHTTPResponse,
    response_body_model=requests.CrosspostMessageHTTPResponseBody,
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
    request_model=requests.DeleteAllMessageReactionsHTTPRequest,
    response_model=requests.DeleteAllMessageReactionsHTTPResponse,
    response_body_model=requests.DeleteAllMessageReactionsHTTPResponseBody,
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
    request_model=requests.DeleteAllMessageReactionsByEmojiHTTPRequest,
    response_model=requests.DeleteAllMessageReactionsByEmojiHTTPResponse,
    response_body_model=requests.DeleteAllMessageReactionsByEmojiHTTPResponseBody,
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
    request_model=requests.ListMessageReactionsByEmojiHTTPRequest,
    response_model=requests.ListMessageReactionsByEmojiHTTPResponse,
    response_body_model=requests.ListMessageReactionsByEmojiHTTPResponseBody,
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
    request_model=requests.DeleteMyMessageReactionHTTPRequest,
    response_model=requests.DeleteMyMessageReactionHTTPResponse,
    response_body_model=requests.DeleteMyMessageReactionHTTPResponseBody,
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
    request_model=requests.AddMyMessageReactionHTTPRequest,
    response_model=requests.AddMyMessageReactionHTTPResponse,
    response_body_model=requests.AddMyMessageReactionHTTPResponseBody,
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
    request_model=requests.DeleteUserMessageReactionHTTPRequest,
    response_model=requests.DeleteUserMessageReactionHTTPResponse,
    response_body_model=requests.DeleteUserMessageReactionHTTPResponseBody,
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
    request_model=requests.CreateThreadFromMessageHTTPRequest,
    response_model=requests.CreateThreadFromMessageHTTPResponse,
    response_body_model=requests.CreateThreadFromMessageHTTPResponseBody,
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
    request_model=requests.DeleteChannelPermissionOverwriteHTTPRequest,
    response_model=requests.DeleteChannelPermissionOverwriteHTTPResponse,
    response_body_model=requests.DeleteChannelPermissionOverwriteHTTPResponseBody,
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
    request_model=requests.SetChannelPermissionOverwriteHTTPRequest,
    response_model=requests.SetChannelPermissionOverwriteHTTPResponse,
    response_body_model=requests.SetChannelPermissionOverwriteHTTPResponseBody,
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
    request_model=requests.DeprecatedListPinsHTTPRequest,
    response_model=requests.DeprecatedListPinsHTTPResponse,
    response_body_model=requests.DeprecatedListPinsHTTPResponseBody,
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
    request_model=requests.DeprecatedDeletePinHTTPRequest,
    response_model=requests.DeprecatedDeletePinHTTPResponse,
    response_body_model=requests.DeprecatedDeletePinHTTPResponseBody,
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
    request_model=requests.DeprecatedCreatePinHTTPRequest,
    response_model=requests.DeprecatedCreatePinHTTPResponse,
    response_body_model=requests.DeprecatedCreatePinHTTPResponseBody,
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
    request_model=requests.GetAnswerVotersHTTPRequest,
    response_model=requests.GetAnswerVotersHTTPResponse,
    response_body_model=requests.GetAnswerVotersHTTPResponseBody,
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
    request_model=requests.PollExpireHTTPRequest,
    response_model=requests.PollExpireHTTPResponse,
    response_body_model=requests.PollExpireHTTPResponseBody,
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
    request_model=requests.DeleteGroupDmUserHTTPRequest,
    response_model=requests.DeleteGroupDmUserHTTPResponse,
    response_body_model=requests.DeleteGroupDmUserHTTPResponseBody,
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
    request_model=requests.AddGroupDmUserHTTPRequest,
    response_model=requests.AddGroupDmUserHTTPResponse,
    response_body_model=requests.AddGroupDmUserHTTPResponseBody,
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
    request_model=requests.SendSoundboardSoundHTTPRequest,
    response_model=requests.SendSoundboardSoundHTTPResponse,
    response_body_model=requests.SendSoundboardSoundHTTPResponseBody,
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
    request_model=requests.ListThreadMembersHTTPRequest,
    response_model=requests.ListThreadMembersHTTPResponse,
    response_body_model=requests.ListThreadMembersHTTPResponseBody,
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
    request_model=requests.LeaveThreadHTTPRequest,
    response_model=requests.LeaveThreadHTTPResponse,
    response_body_model=requests.LeaveThreadHTTPResponseBody,
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
    request_model=requests.JoinThreadHTTPRequest,
    response_model=requests.JoinThreadHTTPResponse,
    response_body_model=requests.JoinThreadHTTPResponseBody,
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
    request_model=requests.DeleteThreadMemberHTTPRequest,
    response_model=requests.DeleteThreadMemberHTTPResponse,
    response_body_model=requests.DeleteThreadMemberHTTPResponseBody,
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
    request_model=requests.GetThreadMemberHTTPRequest,
    response_model=requests.GetThreadMemberHTTPResponse,
    response_body_model=requests.GetThreadMemberHTTPResponseBody,
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
    request_model=requests.AddThreadMemberHTTPRequest,
    response_model=requests.AddThreadMemberHTTPResponse,
    response_body_model=requests.AddThreadMemberHTTPResponseBody,
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
    request_model=requests.CreateThreadHTTPRequest,
    response_model=requests.CreateThreadHTTPResponse,
    response_body_model=requests.CreateThreadHTTPResponseBody,
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
    request_model=requests.ListPrivateArchivedThreadsHTTPRequest,
    response_model=requests.ListPrivateArchivedThreadsHTTPResponse,
    response_body_model=requests.ListPrivateArchivedThreadsHTTPResponseBody,
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
    request_model=requests.ListPublicArchivedThreadsHTTPRequest,
    response_model=requests.ListPublicArchivedThreadsHTTPResponse,
    response_body_model=requests.ListPublicArchivedThreadsHTTPResponseBody,
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
    request_model=requests.ThreadSearchHTTPRequest,
    response_model=requests.ThreadSearchHTTPResponse,
    response_body_model=requests.ThreadSearchHTTPResponseBody,
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
    request_model=requests.TriggerTypingIndicatorHTTPRequest,
    response_model=requests.TriggerTypingIndicatorHTTPResponse,
    response_body_model=requests.TriggerTypingIndicatorHTTPResponseBody,
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
    request_model=requests.ListMyPrivateArchivedThreadsHTTPRequest,
    response_model=requests.ListMyPrivateArchivedThreadsHTTPResponse,
    response_body_model=requests.ListMyPrivateArchivedThreadsHTTPResponseBody,
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
    request_model=requests.UpdateVoiceChannelStatusHTTPRequest,
    response_model=requests.UpdateVoiceChannelStatusHTTPResponse,
    response_body_model=requests.UpdateVoiceChannelStatusHTTPResponseBody,
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
    request_model=requests.ListChannelWebhooksHTTPRequest,
    response_model=requests.ListChannelWebhooksHTTPResponse,
    response_body_model=requests.ListChannelWebhooksHTTPResponseBody,
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
    request_model=requests.CreateWebhookHTTPRequest,
    response_model=requests.CreateWebhookHTTPResponse,
    response_body_model=requests.CreateWebhookHTTPResponseBody,
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
    request_model=requests.GetGatewayHTTPRequest,
    response_model=requests.GetGatewayHTTPResponse,
    response_body_model=requests.GetGatewayHTTPResponseBody,
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
    request_model=requests.GetBotGatewayHTTPRequest,
    response_model=requests.GetBotGatewayHTTPResponse,
    response_body_model=requests.GetBotGatewayHTTPResponseBody,
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
    request_model=requests.GetGuildTemplateHTTPRequest,
    response_model=requests.GetGuildTemplateHTTPResponse,
    response_body_model=requests.GetGuildTemplateHTTPResponseBody,
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
    request_model=requests.GetGuildHTTPRequest,
    response_model=requests.GetGuildHTTPResponse,
    response_body_model=requests.GetGuildHTTPResponseBody,
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
    request_model=requests.UpdateGuildHTTPRequest,
    response_model=requests.UpdateGuildHTTPResponse,
    response_body_model=requests.UpdateGuildHTTPResponseBody,
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
    request_model=requests.ListGuildAuditLogEntriesHTTPRequest,
    response_model=requests.ListGuildAuditLogEntriesHTTPResponse,
    response_body_model=requests.ListGuildAuditLogEntriesHTTPResponseBody,
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
    request_model=requests.ListAutoModerationRulesHTTPRequest,
    response_model=requests.ListAutoModerationRulesHTTPResponse,
    response_body_model=requests.ListAutoModerationRulesHTTPResponseBody,
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
    request_model=requests.CreateAutoModerationRuleHTTPRequest,
    response_model=requests.CreateAutoModerationRuleHTTPResponse,
    response_body_model=requests.CreateAutoModerationRuleHTTPResponseBody,
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
    request_model=requests.DeleteAutoModerationRuleHTTPRequest,
    response_model=requests.DeleteAutoModerationRuleHTTPResponse,
    response_body_model=requests.DeleteAutoModerationRuleHTTPResponseBody,
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
    request_model=requests.GetAutoModerationRuleHTTPRequest,
    response_model=requests.GetAutoModerationRuleHTTPResponse,
    response_body_model=requests.GetAutoModerationRuleHTTPResponseBody,
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
    request_model=requests.UpdateAutoModerationRuleHTTPRequest,
    response_model=requests.UpdateAutoModerationRuleHTTPResponse,
    response_body_model=requests.UpdateAutoModerationRuleHTTPResponseBody,
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
    request_model=requests.ListGuildBansHTTPRequest,
    response_model=requests.ListGuildBansHTTPResponse,
    response_body_model=requests.ListGuildBansHTTPResponseBody,
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
    request_model=requests.UnbanUserFromGuildHTTPRequest,
    response_model=requests.UnbanUserFromGuildHTTPResponse,
    response_body_model=requests.UnbanUserFromGuildHTTPResponseBody,
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
    request_model=requests.GetGuildBanHTTPRequest,
    response_model=requests.GetGuildBanHTTPResponse,
    response_body_model=requests.GetGuildBanHTTPResponseBody,
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
    request_model=requests.BanUserFromGuildHTTPRequest,
    response_model=requests.BanUserFromGuildHTTPResponse,
    response_body_model=requests.BanUserFromGuildHTTPResponseBody,
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
    request_model=requests.BulkBanUsersFromGuildHTTPRequest,
    response_model=requests.BulkBanUsersFromGuildHTTPResponse,
    response_body_model=requests.BulkBanUsersFromGuildHTTPResponseBody,
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
    request_model=requests.ListGuildChannelsHTTPRequest,
    response_model=requests.ListGuildChannelsHTTPResponse,
    response_body_model=requests.ListGuildChannelsHTTPResponseBody,
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
    request_model=requests.BulkUpdateGuildChannelsHTTPRequest,
    response_model=requests.BulkUpdateGuildChannelsHTTPResponse,
    response_body_model=requests.BulkUpdateGuildChannelsHTTPResponseBody,
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
    request_model=requests.CreateGuildChannelHTTPRequest,
    response_model=requests.CreateGuildChannelHTTPResponse,
    response_body_model=requests.CreateGuildChannelHTTPResponseBody,
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
    request_model=requests.ListGuildEmojisHTTPRequest,
    response_model=requests.ListGuildEmojisHTTPResponse,
    response_body_model=requests.ListGuildEmojisHTTPResponseBody,
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
    request_model=requests.CreateGuildEmojiHTTPRequest,
    response_model=requests.CreateGuildEmojiHTTPResponse,
    response_body_model=requests.CreateGuildEmojiHTTPResponseBody,
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
    request_model=requests.DeleteGuildEmojiHTTPRequest,
    response_model=requests.DeleteGuildEmojiHTTPResponse,
    response_body_model=requests.DeleteGuildEmojiHTTPResponseBody,
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
    request_model=requests.GetGuildEmojiHTTPRequest,
    response_model=requests.GetGuildEmojiHTTPResponse,
    response_body_model=requests.GetGuildEmojiHTTPResponseBody,
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
    request_model=requests.UpdateGuildEmojiHTTPRequest,
    response_model=requests.UpdateGuildEmojiHTTPResponse,
    response_body_model=requests.UpdateGuildEmojiHTTPResponseBody,
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
    request_model=requests.UpdateGuildIncidentActionsHTTPRequest,
    response_model=requests.UpdateGuildIncidentActionsHTTPResponse,
    response_body_model=requests.UpdateGuildIncidentActionsHTTPResponseBody,
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
    request_model=requests.ListGuildIntegrationsHTTPRequest,
    response_model=requests.ListGuildIntegrationsHTTPResponse,
    response_body_model=requests.ListGuildIntegrationsHTTPResponseBody,
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
    request_model=requests.DeleteGuildIntegrationHTTPRequest,
    response_model=requests.DeleteGuildIntegrationHTTPResponse,
    response_body_model=requests.DeleteGuildIntegrationHTTPResponseBody,
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
    request_model=requests.ListGuildInvitesHTTPRequest,
    response_model=requests.ListGuildInvitesHTTPResponse,
    response_body_model=requests.ListGuildInvitesHTTPResponseBody,
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
    request_model=requests.ListGuildMembersHTTPRequest,
    response_model=requests.ListGuildMembersHTTPResponse,
    response_body_model=requests.ListGuildMembersHTTPResponseBody,
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
    request_model=requests.UpdateMyGuildMemberHTTPRequest,
    response_model=requests.UpdateMyGuildMemberHTTPResponse,
    response_body_model=requests.UpdateMyGuildMemberHTTPResponseBody,
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
    request_model=requests.SearchGuildMembersHTTPRequest,
    response_model=requests.SearchGuildMembersHTTPResponse,
    response_body_model=requests.SearchGuildMembersHTTPResponseBody,
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
    request_model=requests.DeleteGuildMemberHTTPRequest,
    response_model=requests.DeleteGuildMemberHTTPResponse,
    response_body_model=requests.DeleteGuildMemberHTTPResponseBody,
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
    request_model=requests.GetGuildMemberHTTPRequest,
    response_model=requests.GetGuildMemberHTTPResponse,
    response_body_model=requests.GetGuildMemberHTTPResponseBody,
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
    request_model=requests.UpdateGuildMemberHTTPRequest,
    response_model=requests.UpdateGuildMemberHTTPResponse,
    response_body_model=requests.UpdateGuildMemberHTTPResponseBody,
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
    request_model=requests.AddGuildMemberHTTPRequest,
    response_model=requests.AddGuildMemberHTTPResponse,
    response_body_model=requests.AddGuildMemberHTTPResponseBody,
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
    request_model=requests.DeleteGuildMemberRoleHTTPRequest,
    response_model=requests.DeleteGuildMemberRoleHTTPResponse,
    response_body_model=requests.DeleteGuildMemberRoleHTTPResponseBody,
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
    request_model=requests.AddGuildMemberRoleHTTPRequest,
    response_model=requests.AddGuildMemberRoleHTTPResponse,
    response_body_model=requests.AddGuildMemberRoleHTTPResponseBody,
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
    request_model=requests.GuildSearchHTTPRequest,
    response_model=requests.GuildSearchHTTPResponse,
    response_body_model=requests.GuildSearchHTTPResponseBody,
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
    request_model=requests.GetGuildNewMemberWelcomeHTTPRequest,
    response_model=requests.GetGuildNewMemberWelcomeHTTPResponse,
    response_body_model=requests.GetGuildNewMemberWelcomeHTTPResponseBody,
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
    request_model=requests.GetGuildsOnboardingHTTPRequest,
    response_model=requests.GetGuildsOnboardingHTTPResponse,
    response_body_model=requests.GetGuildsOnboardingHTTPResponseBody,
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
    request_model=requests.PutGuildsOnboardingHTTPRequest,
    response_model=requests.PutGuildsOnboardingHTTPResponse,
    response_body_model=requests.PutGuildsOnboardingHTTPResponseBody,
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
    request_model=requests.GetGuildPreviewHTTPRequest,
    response_model=requests.GetGuildPreviewHTTPResponse,
    response_body_model=requests.GetGuildPreviewHTTPResponseBody,
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
    request_model=requests.PreviewPruneGuildHTTPRequest,
    response_model=requests.PreviewPruneGuildHTTPResponse,
    response_body_model=requests.PreviewPruneGuildHTTPResponseBody,
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
    request_model=requests.PruneGuildHTTPRequest,
    response_model=requests.PruneGuildHTTPResponse,
    response_body_model=requests.PruneGuildHTTPResponseBody,
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
    request_model=requests.ListGuildVoiceRegionsHTTPRequest,
    response_model=requests.ListGuildVoiceRegionsHTTPResponse,
    response_body_model=requests.ListGuildVoiceRegionsHTTPResponseBody,
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
    request_model=requests.GetGuildJoinRequestsHTTPRequest,
    response_model=requests.GetGuildJoinRequestsHTTPResponse,
    response_body_model=requests.GetGuildJoinRequestsHTTPResponseBody,
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
    request_model=requests.ActionGuildJoinRequestHTTPRequest,
    response_model=requests.ActionGuildJoinRequestHTTPResponse,
    response_body_model=requests.ActionGuildJoinRequestHTTPResponseBody,
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
    request_model=requests.ListGuildRolesHTTPRequest,
    response_model=requests.ListGuildRolesHTTPResponse,
    response_body_model=requests.ListGuildRolesHTTPResponseBody,
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
    request_model=requests.BulkUpdateGuildRolesHTTPRequest,
    response_model=requests.BulkUpdateGuildRolesHTTPResponse,
    response_body_model=requests.BulkUpdateGuildRolesHTTPResponseBody,
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
    request_model=requests.CreateGuildRoleHTTPRequest,
    response_model=requests.CreateGuildRoleHTTPResponse,
    response_body_model=requests.CreateGuildRoleHTTPResponseBody,
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
    request_model=requests.GuildRoleMemberCountsHTTPRequest,
    response_model=requests.GuildRoleMemberCountsHTTPResponse,
    response_body_model=requests.GuildRoleMemberCountsHTTPResponseBody,
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
    request_model=requests.DeleteGuildRoleHTTPRequest,
    response_model=requests.DeleteGuildRoleHTTPResponse,
    response_body_model=requests.DeleteGuildRoleHTTPResponseBody,
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
    request_model=requests.GetGuildRoleHTTPRequest,
    response_model=requests.GetGuildRoleHTTPResponse,
    response_body_model=requests.GetGuildRoleHTTPResponseBody,
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
    request_model=requests.UpdateGuildRoleHTTPRequest,
    response_model=requests.UpdateGuildRoleHTTPResponse,
    response_body_model=requests.UpdateGuildRoleHTTPResponseBody,
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
    request_model=requests.ListGuildScheduledEventsHTTPRequest,
    response_model=requests.ListGuildScheduledEventsHTTPResponse,
    response_body_model=requests.ListGuildScheduledEventsHTTPResponseBody,
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
    request_model=requests.CreateGuildScheduledEventHTTPRequest,
    response_model=requests.CreateGuildScheduledEventHTTPResponse,
    response_body_model=requests.CreateGuildScheduledEventHTTPResponseBody,
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
    request_model=requests.DeleteGuildScheduledEventHTTPRequest,
    response_model=requests.DeleteGuildScheduledEventHTTPResponse,
    response_body_model=requests.DeleteGuildScheduledEventHTTPResponseBody,
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
    request_model=requests.GetGuildScheduledEventHTTPRequest,
    response_model=requests.GetGuildScheduledEventHTTPResponse,
    response_body_model=requests.GetGuildScheduledEventHTTPResponseBody,
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
    request_model=requests.UpdateGuildScheduledEventHTTPRequest,
    response_model=requests.UpdateGuildScheduledEventHTTPResponse,
    response_body_model=requests.UpdateGuildScheduledEventHTTPResponseBody,
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
    request_model=requests.CreateGuildScheduledEventExceptionHTTPRequest,
    response_model=requests.CreateGuildScheduledEventExceptionHTTPResponse,
    response_body_model=requests.CreateGuildScheduledEventExceptionHTTPResponseBody,
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
    request_model=requests.DeleteGuildScheduledEventExceptionHTTPRequest,
    response_model=requests.DeleteGuildScheduledEventExceptionHTTPResponse,
    response_body_model=requests.DeleteGuildScheduledEventExceptionHTTPResponseBody,
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
    request_model=requests.UpdateGuildScheduledEventExceptionHTTPRequest,
    response_model=requests.UpdateGuildScheduledEventExceptionHTTPResponse,
    response_body_model=requests.UpdateGuildScheduledEventExceptionHTTPResponseBody,
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
    request_model=requests.ListGuildScheduledEventUsersHTTPRequest,
    response_model=requests.ListGuildScheduledEventUsersHTTPResponse,
    response_body_model=requests.ListGuildScheduledEventUsersHTTPResponseBody,
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
    request_model=requests.CountGuildScheduledEventUsersHTTPRequest,
    response_model=requests.CountGuildScheduledEventUsersHTTPResponse,
    response_body_model=requests.CountGuildScheduledEventUsersHTTPResponseBody,
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
    request_model=requests.ListGuildScheduledEventExceptionUsersHTTPRequest,
    response_model=requests.ListGuildScheduledEventExceptionUsersHTTPResponse,
    response_body_model=requests.ListGuildScheduledEventExceptionUsersHTTPResponseBody,
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
    request_model=requests.ListGuildSoundboardSoundsHTTPRequest,
    response_model=requests.ListGuildSoundboardSoundsHTTPResponse,
    response_body_model=requests.ListGuildSoundboardSoundsHTTPResponseBody,
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
    request_model=requests.CreateGuildSoundboardSoundHTTPRequest,
    response_model=requests.CreateGuildSoundboardSoundHTTPResponse,
    response_body_model=requests.CreateGuildSoundboardSoundHTTPResponseBody,
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
    request_model=requests.DeleteGuildSoundboardSoundHTTPRequest,
    response_model=requests.DeleteGuildSoundboardSoundHTTPResponse,
    response_body_model=requests.DeleteGuildSoundboardSoundHTTPResponseBody,
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
    request_model=requests.GetGuildSoundboardSoundHTTPRequest,
    response_model=requests.GetGuildSoundboardSoundHTTPResponse,
    response_body_model=requests.GetGuildSoundboardSoundHTTPResponseBody,
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
    request_model=requests.UpdateGuildSoundboardSoundHTTPRequest,
    response_model=requests.UpdateGuildSoundboardSoundHTTPResponse,
    response_body_model=requests.UpdateGuildSoundboardSoundHTTPResponseBody,
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
    request_model=requests.ListGuildStickersHTTPRequest,
    response_model=requests.ListGuildStickersHTTPResponse,
    response_body_model=requests.ListGuildStickersHTTPResponseBody,
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
    request_model=requests.CreateGuildStickerHTTPRequest,
    response_model=requests.CreateGuildStickerHTTPResponse,
    response_body_model=requests.CreateGuildStickerHTTPResponseBody,
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
    request_model=requests.DeleteGuildStickerHTTPRequest,
    response_model=requests.DeleteGuildStickerHTTPResponse,
    response_body_model=requests.DeleteGuildStickerHTTPResponseBody,
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
    request_model=requests.GetGuildStickerHTTPRequest,
    response_model=requests.GetGuildStickerHTTPResponse,
    response_body_model=requests.GetGuildStickerHTTPResponseBody,
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
    request_model=requests.UpdateGuildStickerHTTPRequest,
    response_model=requests.UpdateGuildStickerHTTPResponse,
    response_body_model=requests.UpdateGuildStickerHTTPResponseBody,
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
    request_model=requests.ListGuildTemplatesHTTPRequest,
    response_model=requests.ListGuildTemplatesHTTPResponse,
    response_body_model=requests.ListGuildTemplatesHTTPResponseBody,
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
    request_model=requests.CreateGuildTemplateHTTPRequest,
    response_model=requests.CreateGuildTemplateHTTPResponse,
    response_body_model=requests.CreateGuildTemplateHTTPResponseBody,
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
    request_model=requests.DeleteGuildTemplateHTTPRequest,
    response_model=requests.DeleteGuildTemplateHTTPResponse,
    response_body_model=requests.DeleteGuildTemplateHTTPResponseBody,
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
    request_model=requests.UpdateGuildTemplateHTTPRequest,
    response_model=requests.UpdateGuildTemplateHTTPResponse,
    response_body_model=requests.UpdateGuildTemplateHTTPResponseBody,
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
    request_model=requests.SyncGuildTemplateHTTPRequest,
    response_model=requests.SyncGuildTemplateHTTPResponse,
    response_body_model=requests.SyncGuildTemplateHTTPResponseBody,
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
    request_model=requests.GetActiveGuildThreadsHTTPRequest,
    response_model=requests.GetActiveGuildThreadsHTTPResponse,
    response_body_model=requests.GetActiveGuildThreadsHTTPResponseBody,
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
    request_model=requests.GetGuildVanityUrlHTTPRequest,
    response_model=requests.GetGuildVanityUrlHTTPResponse,
    response_body_model=requests.GetGuildVanityUrlHTTPResponseBody,
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
    request_model=requests.GetSelfVoiceStateHTTPRequest,
    response_model=requests.GetSelfVoiceStateHTTPResponse,
    response_body_model=requests.GetSelfVoiceStateHTTPResponseBody,
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
    request_model=requests.UpdateSelfVoiceStateHTTPRequest,
    response_model=requests.UpdateSelfVoiceStateHTTPResponse,
    response_body_model=requests.UpdateSelfVoiceStateHTTPResponseBody,
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
    request_model=requests.GetVoiceStateHTTPRequest,
    response_model=requests.GetVoiceStateHTTPResponse,
    response_body_model=requests.GetVoiceStateHTTPResponseBody,
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
    request_model=requests.UpdateVoiceStateHTTPRequest,
    response_model=requests.UpdateVoiceStateHTTPResponse,
    response_body_model=requests.UpdateVoiceStateHTTPResponseBody,
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
    request_model=requests.GetGuildWebhooksHTTPRequest,
    response_model=requests.GetGuildWebhooksHTTPResponse,
    response_body_model=requests.GetGuildWebhooksHTTPResponseBody,
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
    request_model=requests.GetGuildWelcomeScreenHTTPRequest,
    response_model=requests.GetGuildWelcomeScreenHTTPResponse,
    response_body_model=requests.GetGuildWelcomeScreenHTTPResponseBody,
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
    request_model=requests.UpdateGuildWelcomeScreenHTTPRequest,
    response_model=requests.UpdateGuildWelcomeScreenHTTPResponse,
    response_body_model=requests.UpdateGuildWelcomeScreenHTTPResponseBody,
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
    request_model=requests.GetGuildWidgetSettingsHTTPRequest,
    response_model=requests.GetGuildWidgetSettingsHTTPResponse,
    response_body_model=requests.GetGuildWidgetSettingsHTTPResponseBody,
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
    request_model=requests.UpdateGuildWidgetSettingsHTTPRequest,
    response_model=requests.UpdateGuildWidgetSettingsHTTPResponse,
    response_body_model=requests.UpdateGuildWidgetSettingsHTTPResponseBody,
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
    request_model=requests.GetGuildWidgetHTTPRequest,
    response_model=requests.GetGuildWidgetHTTPResponse,
    response_body_model=requests.GetGuildWidgetHTTPResponseBody,
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
    request_model=requests.GetGuildWidgetPngHTTPRequest,
    response_model=requests.GetGuildWidgetPngHTTPResponse,
    response_body_model=requests.GetGuildWidgetPngHTTPResponseBody,
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
    request_model=requests.CreateInteractionResponseHTTPRequest,
    response_model=requests.CreateInteractionResponseHTTPResponse,
    response_body_model=requests.CreateInteractionResponseHTTPResponseBody,
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
    request_model=requests.InviteRevokeHTTPRequest,
    response_model=requests.InviteRevokeHTTPResponse,
    response_body_model=requests.InviteRevokeHTTPResponseBody,
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
    request_model=requests.InviteResolveHTTPRequest,
    response_model=requests.InviteResolveHTTPResponse,
    response_body_model=requests.InviteResolveHTTPResponseBody,
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
    request_model=requests.GetInviteTargetUsersHTTPRequest,
    response_model=requests.GetInviteTargetUsersHTTPResponse,
    response_body_model=requests.GetInviteTargetUsersHTTPResponseBody,
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
    request_model=requests.UpdateInviteTargetUsersHTTPRequest,
    response_model=requests.UpdateInviteTargetUsersHTTPResponse,
    response_body_model=requests.UpdateInviteTargetUsersHTTPResponseBody,
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
    request_model=requests.GetInviteTargetUsersJobStatusHTTPRequest,
    response_model=requests.GetInviteTargetUsersJobStatusHTTPResponse,
    response_body_model=requests.GetInviteTargetUsersJobStatusHTTPResponseBody,
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
    request_model=requests.CreateLobbyHTTPRequest,
    response_model=requests.CreateLobbyHTTPResponse,
    response_body_model=requests.CreateLobbyHTTPResponseBody,
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
    request_model=requests.CreateOrJoinLobbyHTTPRequest,
    response_model=requests.CreateOrJoinLobbyHTTPResponse,
    response_body_model=requests.CreateOrJoinLobbyHTTPResponseBody,
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
    request_model=requests.DeleteLobbyHTTPRequest,
    response_model=requests.DeleteLobbyHTTPResponse,
    response_body_model=requests.DeleteLobbyHTTPResponseBody,
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
    request_model=requests.GetLobbyHTTPRequest,
    response_model=requests.GetLobbyHTTPResponse,
    response_body_model=requests.GetLobbyHTTPResponseBody,
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
    request_model=requests.EditLobbyHTTPRequest,
    response_model=requests.EditLobbyHTTPResponse,
    response_body_model=requests.EditLobbyHTTPResponseBody,
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
    request_model=requests.EditLobbyChannelLinkHTTPRequest,
    response_model=requests.EditLobbyChannelLinkHTTPResponse,
    response_body_model=requests.EditLobbyChannelLinkHTTPResponseBody,
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
    request_model=requests.LeaveLobbyHTTPRequest,
    response_model=requests.LeaveLobbyHTTPResponse,
    response_body_model=requests.LeaveLobbyHTTPResponseBody,
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
    request_model=requests.CreateLinkedLobbyGuildInviteForSelfHTTPRequest,
    response_model=requests.CreateLinkedLobbyGuildInviteForSelfHTTPResponse,
    response_body_model=requests.CreateLinkedLobbyGuildInviteForSelfHTTPResponseBody,
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
    request_model=requests.BulkUpdateLobbyMembersHTTPRequest,
    response_model=requests.BulkUpdateLobbyMembersHTTPResponse,
    response_body_model=requests.BulkUpdateLobbyMembersHTTPResponseBody,
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
    request_model=requests.DeleteLobbyMemberHTTPRequest,
    response_model=requests.DeleteLobbyMemberHTTPResponse,
    response_body_model=requests.DeleteLobbyMemberHTTPResponseBody,
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
    request_model=requests.AddLobbyMemberHTTPRequest,
    response_model=requests.AddLobbyMemberHTTPResponse,
    response_body_model=requests.AddLobbyMemberHTTPResponseBody,
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
    request_model=requests.CreateLinkedLobbyGuildInviteForUserHTTPRequest,
    response_model=requests.CreateLinkedLobbyGuildInviteForUserHTTPResponse,
    response_body_model=requests.CreateLinkedLobbyGuildInviteForUserHTTPResponseBody,
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
    request_model=requests.GetLobbyMessagesHTTPRequest,
    response_model=requests.GetLobbyMessagesHTTPResponse,
    response_body_model=requests.GetLobbyMessagesHTTPResponseBody,
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
    request_model=requests.CreateLobbyMessageHTTPRequest,
    response_model=requests.CreateLobbyMessageHTTPResponse,
    response_body_model=requests.CreateLobbyMessageHTTPResponseBody,
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
    request_model=requests.UpdateLobbyMessageExternalModerationMetadataHTTPRequest,
    response_model=requests.UpdateLobbyMessageExternalModerationMetadataHTTPResponse,
    response_body_model=requests.UpdateLobbyMessageExternalModerationMetadataHTTPResponseBody,
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
    request_model=requests.GetMyOauth2AuthorizationHTTPRequest,
    response_model=requests.GetMyOauth2AuthorizationHTTPResponse,
    response_body_model=requests.GetMyOauth2AuthorizationHTTPResponseBody,
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
    request_model=requests.GetMyOauth2ApplicationHTTPRequest,
    response_model=requests.GetMyOauth2ApplicationHTTPResponse,
    response_body_model=requests.GetMyOauth2ApplicationHTTPResponseBody,
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
    request_model=requests.GetPublicKeysHTTPRequest,
    response_model=requests.GetPublicKeysHTTPResponse,
    response_body_model=requests.GetPublicKeysHTTPResponseBody,
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
    request_model=requests.GetOpenidConnectUserinfoHTTPRequest,
    response_model=requests.GetOpenidConnectUserinfoHTTPResponse,
    response_body_model=requests.GetOpenidConnectUserinfoHTTPResponseBody,
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
    request_model=requests.UpdateUserMessageExternalModerationMetadataHTTPRequest,
    response_model=requests.UpdateUserMessageExternalModerationMetadataHTTPResponse,
    response_body_model=requests.UpdateUserMessageExternalModerationMetadataHTTPResponseBody,
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
    request_model=requests.PartnerSdkUnmergeProvisionalAccountHTTPRequest,
    response_model=requests.PartnerSdkUnmergeProvisionalAccountHTTPResponse,
    response_body_model=requests.PartnerSdkUnmergeProvisionalAccountHTTPResponseBody,
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
    request_model=requests.BotPartnerSdkUnmergeProvisionalAccountHTTPRequest,
    response_model=requests.BotPartnerSdkUnmergeProvisionalAccountHTTPResponse,
    response_body_model=requests.BotPartnerSdkUnmergeProvisionalAccountHTTPResponseBody,
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
    request_model=requests.PartnerSdkTokenHTTPRequest,
    response_model=requests.PartnerSdkTokenHTTPResponse,
    response_body_model=requests.PartnerSdkTokenHTTPResponseBody,
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
    request_model=requests.BotPartnerSdkTokenHTTPRequest,
    response_model=requests.BotPartnerSdkTokenHTTPResponse,
    response_body_model=requests.BotPartnerSdkTokenHTTPResponseBody,
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
    request_model=requests.GetSkuSubscriptionsHTTPRequest,
    response_model=requests.GetSkuSubscriptionsHTTPResponse,
    response_body_model=requests.GetSkuSubscriptionsHTTPResponseBody,
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
    request_model=requests.GetSkuSubscriptionHTTPRequest,
    response_model=requests.GetSkuSubscriptionHTTPResponse,
    response_body_model=requests.GetSkuSubscriptionHTTPResponseBody,
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
    request_model=requests.GetSoundboardDefaultSoundsHTTPRequest,
    response_model=requests.GetSoundboardDefaultSoundsHTTPResponse,
    response_body_model=requests.GetSoundboardDefaultSoundsHTTPResponseBody,
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
    request_model=requests.CreateStageInstanceHTTPRequest,
    response_model=requests.CreateStageInstanceHTTPResponse,
    response_body_model=requests.CreateStageInstanceHTTPResponseBody,
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
    request_model=requests.DeleteStageInstanceHTTPRequest,
    response_model=requests.DeleteStageInstanceHTTPResponse,
    response_body_model=requests.DeleteStageInstanceHTTPResponseBody,
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
    request_model=requests.GetStageInstanceHTTPRequest,
    response_model=requests.GetStageInstanceHTTPResponse,
    response_body_model=requests.GetStageInstanceHTTPResponseBody,
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
    request_model=requests.UpdateStageInstanceHTTPRequest,
    response_model=requests.UpdateStageInstanceHTTPResponse,
    response_body_model=requests.UpdateStageInstanceHTTPResponseBody,
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
    request_model=requests.ListStickerPacksHTTPRequest,
    response_model=requests.ListStickerPacksHTTPResponse,
    response_body_model=requests.ListStickerPacksHTTPResponseBody,
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
    request_model=requests.GetStickerPackHTTPRequest,
    response_model=requests.GetStickerPackHTTPResponse,
    response_body_model=requests.GetStickerPackHTTPResponseBody,
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
    request_model=requests.GetStickerHTTPRequest,
    response_model=requests.GetStickerHTTPResponse,
    response_body_model=requests.GetStickerHTTPResponseBody,
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
    request_model=requests.GetMyUserHTTPRequest,
    response_model=requests.GetMyUserHTTPResponse,
    response_body_model=requests.GetMyUserHTTPResponseBody,
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
    request_model=requests.UpdateMyUserHTTPRequest,
    response_model=requests.UpdateMyUserHTTPResponse,
    response_body_model=requests.UpdateMyUserHTTPResponseBody,
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
    request_model=requests.GetCurrentUserApplicationEntitlementsHTTPRequest,
    response_model=requests.GetCurrentUserApplicationEntitlementsHTTPResponse,
    response_body_model=requests.GetCurrentUserApplicationEntitlementsHTTPResponseBody,
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
    request_model=requests.DeleteApplicationUserRoleConnectionHTTPRequest,
    response_model=requests.DeleteApplicationUserRoleConnectionHTTPResponse,
    response_body_model=requests.DeleteApplicationUserRoleConnectionHTTPResponseBody,
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
    request_model=requests.GetApplicationUserRoleConnectionHTTPRequest,
    response_model=requests.GetApplicationUserRoleConnectionHTTPResponse,
    response_body_model=requests.GetApplicationUserRoleConnectionHTTPResponseBody,
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
    request_model=requests.UpdateApplicationUserRoleConnectionHTTPRequest,
    response_model=requests.UpdateApplicationUserRoleConnectionHTTPResponse,
    response_body_model=requests.UpdateApplicationUserRoleConnectionHTTPResponseBody,
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
    request_model=requests.CreateDmHTTPRequest,
    response_model=requests.CreateDmHTTPResponse,
    response_body_model=requests.CreateDmHTTPResponseBody,
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
    request_model=requests.ListMyConnectionsHTTPRequest,
    response_model=requests.ListMyConnectionsHTTPResponse,
    response_body_model=requests.ListMyConnectionsHTTPResponseBody,
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
    request_model=requests.ListMyGuildsHTTPRequest,
    response_model=requests.ListMyGuildsHTTPResponse,
    response_body_model=requests.ListMyGuildsHTTPResponseBody,
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
    request_model=requests.LeaveGuildHTTPRequest,
    response_model=requests.LeaveGuildHTTPResponse,
    response_body_model=requests.LeaveGuildHTTPResponseBody,
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
    request_model=requests.GetMyGuildMemberHTTPRequest,
    response_model=requests.GetMyGuildMemberHTTPResponse,
    response_body_model=requests.GetMyGuildMemberHTTPResponseBody,
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
    request_model=requests.GetUserHTTPRequest,
    response_model=requests.GetUserHTTPResponse,
    response_body_model=requests.GetUserHTTPResponseBody,
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
    request_model=requests.ListVoiceRegionsHTTPRequest,
    response_model=requests.ListVoiceRegionsHTTPResponse,
    response_body_model=requests.ListVoiceRegionsHTTPResponseBody,
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
    request_model=requests.DeleteWebhookHTTPRequest,
    response_model=requests.DeleteWebhookHTTPResponse,
    response_body_model=requests.DeleteWebhookHTTPResponseBody,
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
    request_model=requests.GetWebhookHTTPRequest,
    response_model=requests.GetWebhookHTTPResponse,
    response_body_model=requests.GetWebhookHTTPResponseBody,
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
    request_model=requests.UpdateWebhookHTTPRequest,
    response_model=requests.UpdateWebhookHTTPResponse,
    response_body_model=requests.UpdateWebhookHTTPResponseBody,
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
    request_model=requests.DeleteWebhookByTokenHTTPRequest,
    response_model=requests.DeleteWebhookByTokenHTTPResponse,
    response_body_model=requests.DeleteWebhookByTokenHTTPResponseBody,
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
    request_model=requests.GetWebhookByTokenHTTPRequest,
    response_model=requests.GetWebhookByTokenHTTPResponse,
    response_body_model=requests.GetWebhookByTokenHTTPResponseBody,
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
    request_model=requests.UpdateWebhookByTokenHTTPRequest,
    response_model=requests.UpdateWebhookByTokenHTTPResponse,
    response_body_model=requests.UpdateWebhookByTokenHTTPResponseBody,
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
    request_model=requests.ExecuteWebhookHTTPRequest,
    response_model=requests.ExecuteWebhookHTTPResponse,
    response_body_model=requests.ExecuteWebhookHTTPResponseBody,
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
    request_model=requests.ExecuteGithubCompatibleWebhookHTTPRequest,
    response_model=requests.ExecuteGithubCompatibleWebhookHTTPResponse,
    response_body_model=requests.ExecuteGithubCompatibleWebhookHTTPResponseBody,
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
    request_model=requests.DeleteOriginalWebhookMessageHTTPRequest,
    response_model=requests.DeleteOriginalWebhookMessageHTTPResponse,
    response_body_model=requests.DeleteOriginalWebhookMessageHTTPResponseBody,
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
    request_model=requests.GetOriginalWebhookMessageHTTPRequest,
    response_model=requests.GetOriginalWebhookMessageHTTPResponse,
    response_body_model=requests.GetOriginalWebhookMessageHTTPResponseBody,
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
    request_model=requests.UpdateOriginalWebhookMessageHTTPRequest,
    response_model=requests.UpdateOriginalWebhookMessageHTTPResponse,
    response_body_model=requests.UpdateOriginalWebhookMessageHTTPResponseBody,
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
    request_model=requests.DeleteWebhookMessageHTTPRequest,
    response_model=requests.DeleteWebhookMessageHTTPResponse,
    response_body_model=requests.DeleteWebhookMessageHTTPResponseBody,
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
    request_model=requests.GetWebhookMessageHTTPRequest,
    response_model=requests.GetWebhookMessageHTTPResponse,
    response_body_model=requests.GetWebhookMessageHTTPResponseBody,
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
    request_model=requests.UpdateWebhookMessageHTTPRequest,
    response_model=requests.UpdateWebhookMessageHTTPResponse,
    response_body_model=requests.UpdateWebhookMessageHTTPResponseBody,
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
    request_model=requests.ExecuteSlackCompatibleWebhookHTTPRequest,
    response_model=requests.ExecuteSlackCompatibleWebhookHTTPResponse,
    response_body_model=requests.ExecuteSlackCompatibleWebhookHTTPResponseBody,
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


class GeneratedDiscordHTTPClient:
  async def _request_operation(
    self, operation: DiscordOperationId, request: BaseModel
  ) -> BaseModel:
    raise NotImplementedError

  async def get_my_application(
    self, request: requests.GetMyApplicationHTTPRequest
  ) -> requests.GetMyApplicationHTTPResponse:
    response = await self._request_operation("get_my_application", request)
    if not isinstance(response, requests.GetMyApplicationHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_my_application(
    self, request: requests.UpdateMyApplicationHTTPRequest
  ) -> requests.UpdateMyApplicationHTTPResponse:
    response = await self._request_operation("update_my_application", request)
    if not isinstance(response, requests.UpdateMyApplicationHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_application(
    self, request: requests.GetApplicationHTTPRequest
  ) -> requests.GetApplicationHTTPResponse:
    response = await self._request_operation("get_application", request)
    if not isinstance(response, requests.GetApplicationHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_application(
    self, request: requests.UpdateApplicationHTTPRequest
  ) -> requests.UpdateApplicationHTTPResponse:
    response = await self._request_operation("update_application", request)
    if not isinstance(response, requests.UpdateApplicationHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def applications_get_activity_instance(
    self, request: requests.ApplicationsGetActivityInstanceHTTPRequest
  ) -> requests.ApplicationsGetActivityInstanceHTTPResponse:
    response = await self._request_operation(
      "applications_get_activity_instance", request
    )
    if not isinstance(response, requests.ApplicationsGetActivityInstanceHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def upload_application_attachment(
    self, request: requests.UploadApplicationAttachmentHTTPRequest
  ) -> requests.UploadApplicationAttachmentHTTPResponse:
    response = await self._request_operation("upload_application_attachment", request)
    if not isinstance(response, requests.UploadApplicationAttachmentHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_application_commands(
    self, request: requests.ListApplicationCommandsHTTPRequest
  ) -> requests.ListApplicationCommandsHTTPResponse:
    response = await self._request_operation("list_application_commands", request)
    if not isinstance(response, requests.ListApplicationCommandsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_application_command(
    self, request: requests.CreateApplicationCommandHTTPRequest
  ) -> requests.CreateApplicationCommandHTTPResponse:
    response = await self._request_operation("create_application_command", request)
    if not isinstance(response, requests.CreateApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bulk_set_application_commands(
    self, request: requests.BulkSetApplicationCommandsHTTPRequest
  ) -> requests.BulkSetApplicationCommandsHTTPResponse:
    response = await self._request_operation("bulk_set_application_commands", request)
    if not isinstance(response, requests.BulkSetApplicationCommandsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_application_command(
    self, request: requests.DeleteApplicationCommandHTTPRequest
  ) -> requests.DeleteApplicationCommandHTTPResponse:
    response = await self._request_operation("delete_application_command", request)
    if not isinstance(response, requests.DeleteApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_application_command(
    self, request: requests.GetApplicationCommandHTTPRequest
  ) -> requests.GetApplicationCommandHTTPResponse:
    response = await self._request_operation("get_application_command", request)
    if not isinstance(response, requests.GetApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_application_command(
    self, request: requests.UpdateApplicationCommandHTTPRequest
  ) -> requests.UpdateApplicationCommandHTTPResponse:
    response = await self._request_operation("update_application_command", request)
    if not isinstance(response, requests.UpdateApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_application_emojis(
    self, request: requests.ListApplicationEmojisHTTPRequest
  ) -> requests.ListApplicationEmojisHTTPResponse:
    response = await self._request_operation("list_application_emojis", request)
    if not isinstance(response, requests.ListApplicationEmojisHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_application_emoji(
    self, request: requests.CreateApplicationEmojiHTTPRequest
  ) -> requests.CreateApplicationEmojiHTTPResponse:
    response = await self._request_operation("create_application_emoji", request)
    if not isinstance(response, requests.CreateApplicationEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_application_emoji(
    self, request: requests.DeleteApplicationEmojiHTTPRequest
  ) -> requests.DeleteApplicationEmojiHTTPResponse:
    response = await self._request_operation("delete_application_emoji", request)
    if not isinstance(response, requests.DeleteApplicationEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_application_emoji(
    self, request: requests.GetApplicationEmojiHTTPRequest
  ) -> requests.GetApplicationEmojiHTTPResponse:
    response = await self._request_operation("get_application_emoji", request)
    if not isinstance(response, requests.GetApplicationEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_application_emoji(
    self, request: requests.UpdateApplicationEmojiHTTPRequest
  ) -> requests.UpdateApplicationEmojiHTTPResponse:
    response = await self._request_operation("update_application_emoji", request)
    if not isinstance(response, requests.UpdateApplicationEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_entitlements(
    self, request: requests.GetEntitlementsHTTPRequest
  ) -> requests.GetEntitlementsHTTPResponse:
    response = await self._request_operation("get_entitlements", request)
    if not isinstance(response, requests.GetEntitlementsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_entitlement(
    self, request: requests.CreateEntitlementHTTPRequest
  ) -> requests.CreateEntitlementHTTPResponse:
    response = await self._request_operation("create_entitlement", request)
    if not isinstance(response, requests.CreateEntitlementHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_entitlement(
    self, request: requests.DeleteEntitlementHTTPRequest
  ) -> requests.DeleteEntitlementHTTPResponse:
    response = await self._request_operation("delete_entitlement", request)
    if not isinstance(response, requests.DeleteEntitlementHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_entitlement(
    self, request: requests.GetEntitlementHTTPRequest
  ) -> requests.GetEntitlementHTTPResponse:
    response = await self._request_operation("get_entitlement", request)
    if not isinstance(response, requests.GetEntitlementHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def consume_entitlement(
    self, request: requests.ConsumeEntitlementHTTPRequest
  ) -> requests.ConsumeEntitlementHTTPResponse:
    response = await self._request_operation("consume_entitlement", request)
    if not isinstance(response, requests.ConsumeEntitlementHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_application_commands(
    self, request: requests.ListGuildApplicationCommandsHTTPRequest
  ) -> requests.ListGuildApplicationCommandsHTTPResponse:
    response = await self._request_operation("list_guild_application_commands", request)
    if not isinstance(response, requests.ListGuildApplicationCommandsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_application_command(
    self, request: requests.CreateGuildApplicationCommandHTTPRequest
  ) -> requests.CreateGuildApplicationCommandHTTPResponse:
    response = await self._request_operation(
      "create_guild_application_command", request
    )
    if not isinstance(response, requests.CreateGuildApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bulk_set_guild_application_commands(
    self, request: requests.BulkSetGuildApplicationCommandsHTTPRequest
  ) -> requests.BulkSetGuildApplicationCommandsHTTPResponse:
    response = await self._request_operation(
      "bulk_set_guild_application_commands", request
    )
    if not isinstance(response, requests.BulkSetGuildApplicationCommandsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_application_command_permissions(
    self, request: requests.ListGuildApplicationCommandPermissionsHTTPRequest
  ) -> requests.ListGuildApplicationCommandPermissionsHTTPResponse:
    response = await self._request_operation(
      "list_guild_application_command_permissions", request
    )
    if not isinstance(
      response, requests.ListGuildApplicationCommandPermissionsHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_application_command(
    self, request: requests.DeleteGuildApplicationCommandHTTPRequest
  ) -> requests.DeleteGuildApplicationCommandHTTPResponse:
    response = await self._request_operation(
      "delete_guild_application_command", request
    )
    if not isinstance(response, requests.DeleteGuildApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_application_command(
    self, request: requests.GetGuildApplicationCommandHTTPRequest
  ) -> requests.GetGuildApplicationCommandHTTPResponse:
    response = await self._request_operation("get_guild_application_command", request)
    if not isinstance(response, requests.GetGuildApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_application_command(
    self, request: requests.UpdateGuildApplicationCommandHTTPRequest
  ) -> requests.UpdateGuildApplicationCommandHTTPResponse:
    response = await self._request_operation(
      "update_guild_application_command", request
    )
    if not isinstance(response, requests.UpdateGuildApplicationCommandHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_application_command_permissions(
    self, request: requests.GetGuildApplicationCommandPermissionsHTTPRequest
  ) -> requests.GetGuildApplicationCommandPermissionsHTTPResponse:
    response = await self._request_operation(
      "get_guild_application_command_permissions", request
    )
    if not isinstance(
      response, requests.GetGuildApplicationCommandPermissionsHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def set_guild_application_command_permissions(
    self, request: requests.SetGuildApplicationCommandPermissionsHTTPRequest
  ) -> requests.SetGuildApplicationCommandPermissionsHTTPResponse:
    response = await self._request_operation(
      "set_guild_application_command_permissions", request
    )
    if not isinstance(
      response, requests.SetGuildApplicationCommandPermissionsHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_application_role_connections_metadata(
    self, request: requests.GetApplicationRoleConnectionsMetadataHTTPRequest
  ) -> requests.GetApplicationRoleConnectionsMetadataHTTPResponse:
    response = await self._request_operation(
      "get_application_role_connections_metadata", request
    )
    if not isinstance(
      response, requests.GetApplicationRoleConnectionsMetadataHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_application_role_connections_metadata(
    self, request: requests.UpdateApplicationRoleConnectionsMetadataHTTPRequest
  ) -> requests.UpdateApplicationRoleConnectionsMetadataHTTPResponse:
    response = await self._request_operation(
      "update_application_role_connections_metadata", request
    )
    if not isinstance(
      response, requests.UpdateApplicationRoleConnectionsMetadataHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_channel(
    self, request: requests.DeleteChannelHTTPRequest
  ) -> requests.DeleteChannelHTTPResponse:
    response = await self._request_operation("delete_channel", request)
    if not isinstance(response, requests.DeleteChannelHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_channel(
    self, request: requests.GetChannelHTTPRequest
  ) -> requests.GetChannelHTTPResponse:
    response = await self._request_operation("get_channel", request)
    if not isinstance(response, requests.GetChannelHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_channel(
    self, request: requests.UpdateChannelHTTPRequest
  ) -> requests.UpdateChannelHTTPResponse:
    response = await self._request_operation("update_channel", request)
    if not isinstance(response, requests.UpdateChannelHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def follow_channel(
    self, request: requests.FollowChannelHTTPRequest
  ) -> requests.FollowChannelHTTPResponse:
    response = await self._request_operation("follow_channel", request)
    if not isinstance(response, requests.FollowChannelHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_channel_invites(
    self, request: requests.ListChannelInvitesHTTPRequest
  ) -> requests.ListChannelInvitesHTTPResponse:
    response = await self._request_operation("list_channel_invites", request)
    if not isinstance(response, requests.ListChannelInvitesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_channel_invite(
    self, request: requests.CreateChannelInviteHTTPRequest
  ) -> requests.CreateChannelInviteHTTPResponse:
    response = await self._request_operation("create_channel_invite", request)
    if not isinstance(response, requests.CreateChannelInviteHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_messages(
    self, request: requests.ListMessagesHTTPRequest
  ) -> requests.ListMessagesHTTPResponse:
    response = await self._request_operation("list_messages", request)
    if not isinstance(response, requests.ListMessagesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_message(
    self, request: requests.CreateMessageHTTPRequest
  ) -> requests.CreateMessageHTTPResponse:
    response = await self._request_operation("create_message", request)
    if not isinstance(response, requests.CreateMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bulk_delete_messages(
    self, request: requests.BulkDeleteMessagesHTTPRequest
  ) -> requests.BulkDeleteMessagesHTTPResponse:
    response = await self._request_operation("bulk_delete_messages", request)
    if not isinstance(response, requests.BulkDeleteMessagesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_pins(
    self, request: requests.ListPinsHTTPRequest
  ) -> requests.ListPinsHTTPResponse:
    response = await self._request_operation("list_pins", request)
    if not isinstance(response, requests.ListPinsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_pin(
    self, request: requests.DeletePinHTTPRequest
  ) -> requests.DeletePinHTTPResponse:
    response = await self._request_operation("delete_pin", request)
    if not isinstance(response, requests.DeletePinHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_pin(
    self, request: requests.CreatePinHTTPRequest
  ) -> requests.CreatePinHTTPResponse:
    response = await self._request_operation("create_pin", request)
    if not isinstance(response, requests.CreatePinHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_message(
    self, request: requests.DeleteMessageHTTPRequest
  ) -> requests.DeleteMessageHTTPResponse:
    response = await self._request_operation("delete_message", request)
    if not isinstance(response, requests.DeleteMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_message(
    self, request: requests.GetMessageHTTPRequest
  ) -> requests.GetMessageHTTPResponse:
    response = await self._request_operation("get_message", request)
    if not isinstance(response, requests.GetMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_message(
    self, request: requests.UpdateMessageHTTPRequest
  ) -> requests.UpdateMessageHTTPResponse:
    response = await self._request_operation("update_message", request)
    if not isinstance(response, requests.UpdateMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def crosspost_message(
    self, request: requests.CrosspostMessageHTTPRequest
  ) -> requests.CrosspostMessageHTTPResponse:
    response = await self._request_operation("crosspost_message", request)
    if not isinstance(response, requests.CrosspostMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_all_message_reactions(
    self, request: requests.DeleteAllMessageReactionsHTTPRequest
  ) -> requests.DeleteAllMessageReactionsHTTPResponse:
    response = await self._request_operation("delete_all_message_reactions", request)
    if not isinstance(response, requests.DeleteAllMessageReactionsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_all_message_reactions_by_emoji(
    self, request: requests.DeleteAllMessageReactionsByEmojiHTTPRequest
  ) -> requests.DeleteAllMessageReactionsByEmojiHTTPResponse:
    response = await self._request_operation(
      "delete_all_message_reactions_by_emoji", request
    )
    if not isinstance(response, requests.DeleteAllMessageReactionsByEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_message_reactions_by_emoji(
    self, request: requests.ListMessageReactionsByEmojiHTTPRequest
  ) -> requests.ListMessageReactionsByEmojiHTTPResponse:
    response = await self._request_operation("list_message_reactions_by_emoji", request)
    if not isinstance(response, requests.ListMessageReactionsByEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_my_message_reaction(
    self, request: requests.DeleteMyMessageReactionHTTPRequest
  ) -> requests.DeleteMyMessageReactionHTTPResponse:
    response = await self._request_operation("delete_my_message_reaction", request)
    if not isinstance(response, requests.DeleteMyMessageReactionHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def add_my_message_reaction(
    self, request: requests.AddMyMessageReactionHTTPRequest
  ) -> requests.AddMyMessageReactionHTTPResponse:
    response = await self._request_operation("add_my_message_reaction", request)
    if not isinstance(response, requests.AddMyMessageReactionHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_user_message_reaction(
    self, request: requests.DeleteUserMessageReactionHTTPRequest
  ) -> requests.DeleteUserMessageReactionHTTPResponse:
    response = await self._request_operation("delete_user_message_reaction", request)
    if not isinstance(response, requests.DeleteUserMessageReactionHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_thread_from_message(
    self, request: requests.CreateThreadFromMessageHTTPRequest
  ) -> requests.CreateThreadFromMessageHTTPResponse:
    response = await self._request_operation("create_thread_from_message", request)
    if not isinstance(response, requests.CreateThreadFromMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_channel_permission_overwrite(
    self, request: requests.DeleteChannelPermissionOverwriteHTTPRequest
  ) -> requests.DeleteChannelPermissionOverwriteHTTPResponse:
    response = await self._request_operation(
      "delete_channel_permission_overwrite", request
    )
    if not isinstance(response, requests.DeleteChannelPermissionOverwriteHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def set_channel_permission_overwrite(
    self, request: requests.SetChannelPermissionOverwriteHTTPRequest
  ) -> requests.SetChannelPermissionOverwriteHTTPResponse:
    response = await self._request_operation(
      "set_channel_permission_overwrite", request
    )
    if not isinstance(response, requests.SetChannelPermissionOverwriteHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def deprecated_list_pins(
    self, request: requests.DeprecatedListPinsHTTPRequest
  ) -> requests.DeprecatedListPinsHTTPResponse:
    response = await self._request_operation("deprecated_list_pins", request)
    if not isinstance(response, requests.DeprecatedListPinsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def deprecated_delete_pin(
    self, request: requests.DeprecatedDeletePinHTTPRequest
  ) -> requests.DeprecatedDeletePinHTTPResponse:
    response = await self._request_operation("deprecated_delete_pin", request)
    if not isinstance(response, requests.DeprecatedDeletePinHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def deprecated_create_pin(
    self, request: requests.DeprecatedCreatePinHTTPRequest
  ) -> requests.DeprecatedCreatePinHTTPResponse:
    response = await self._request_operation("deprecated_create_pin", request)
    if not isinstance(response, requests.DeprecatedCreatePinHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_answer_voters(
    self, request: requests.GetAnswerVotersHTTPRequest
  ) -> requests.GetAnswerVotersHTTPResponse:
    response = await self._request_operation("get_answer_voters", request)
    if not isinstance(response, requests.GetAnswerVotersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def poll_expire(
    self, request: requests.PollExpireHTTPRequest
  ) -> requests.PollExpireHTTPResponse:
    response = await self._request_operation("poll_expire", request)
    if not isinstance(response, requests.PollExpireHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_group_dm_user(
    self, request: requests.DeleteGroupDmUserHTTPRequest
  ) -> requests.DeleteGroupDmUserHTTPResponse:
    response = await self._request_operation("delete_group_dm_user", request)
    if not isinstance(response, requests.DeleteGroupDmUserHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def add_group_dm_user(
    self, request: requests.AddGroupDmUserHTTPRequest
  ) -> requests.AddGroupDmUserHTTPResponse:
    response = await self._request_operation("add_group_dm_user", request)
    if not isinstance(response, requests.AddGroupDmUserHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def send_soundboard_sound(
    self, request: requests.SendSoundboardSoundHTTPRequest
  ) -> requests.SendSoundboardSoundHTTPResponse:
    response = await self._request_operation("send_soundboard_sound", request)
    if not isinstance(response, requests.SendSoundboardSoundHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_thread_members(
    self, request: requests.ListThreadMembersHTTPRequest
  ) -> requests.ListThreadMembersHTTPResponse:
    response = await self._request_operation("list_thread_members", request)
    if not isinstance(response, requests.ListThreadMembersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def leave_thread(
    self, request: requests.LeaveThreadHTTPRequest
  ) -> requests.LeaveThreadHTTPResponse:
    response = await self._request_operation("leave_thread", request)
    if not isinstance(response, requests.LeaveThreadHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def join_thread(
    self, request: requests.JoinThreadHTTPRequest
  ) -> requests.JoinThreadHTTPResponse:
    response = await self._request_operation("join_thread", request)
    if not isinstance(response, requests.JoinThreadHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_thread_member(
    self, request: requests.DeleteThreadMemberHTTPRequest
  ) -> requests.DeleteThreadMemberHTTPResponse:
    response = await self._request_operation("delete_thread_member", request)
    if not isinstance(response, requests.DeleteThreadMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_thread_member(
    self, request: requests.GetThreadMemberHTTPRequest
  ) -> requests.GetThreadMemberHTTPResponse:
    response = await self._request_operation("get_thread_member", request)
    if not isinstance(response, requests.GetThreadMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def add_thread_member(
    self, request: requests.AddThreadMemberHTTPRequest
  ) -> requests.AddThreadMemberHTTPResponse:
    response = await self._request_operation("add_thread_member", request)
    if not isinstance(response, requests.AddThreadMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_thread(
    self, request: requests.CreateThreadHTTPRequest
  ) -> requests.CreateThreadHTTPResponse:
    response = await self._request_operation("create_thread", request)
    if not isinstance(response, requests.CreateThreadHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_private_archived_threads(
    self, request: requests.ListPrivateArchivedThreadsHTTPRequest
  ) -> requests.ListPrivateArchivedThreadsHTTPResponse:
    response = await self._request_operation("list_private_archived_threads", request)
    if not isinstance(response, requests.ListPrivateArchivedThreadsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_public_archived_threads(
    self, request: requests.ListPublicArchivedThreadsHTTPRequest
  ) -> requests.ListPublicArchivedThreadsHTTPResponse:
    response = await self._request_operation("list_public_archived_threads", request)
    if not isinstance(response, requests.ListPublicArchivedThreadsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def thread_search(
    self, request: requests.ThreadSearchHTTPRequest
  ) -> requests.ThreadSearchHTTPResponse:
    response = await self._request_operation("thread_search", request)
    if not isinstance(response, requests.ThreadSearchHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def trigger_typing_indicator(
    self, request: requests.TriggerTypingIndicatorHTTPRequest
  ) -> requests.TriggerTypingIndicatorHTTPResponse:
    response = await self._request_operation("trigger_typing_indicator", request)
    if not isinstance(response, requests.TriggerTypingIndicatorHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_my_private_archived_threads(
    self, request: requests.ListMyPrivateArchivedThreadsHTTPRequest
  ) -> requests.ListMyPrivateArchivedThreadsHTTPResponse:
    response = await self._request_operation(
      "list_my_private_archived_threads", request
    )
    if not isinstance(response, requests.ListMyPrivateArchivedThreadsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_voice_channel_status(
    self, request: requests.UpdateVoiceChannelStatusHTTPRequest
  ) -> requests.UpdateVoiceChannelStatusHTTPResponse:
    response = await self._request_operation("update_voice_channel_status", request)
    if not isinstance(response, requests.UpdateVoiceChannelStatusHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_channel_webhooks(
    self, request: requests.ListChannelWebhooksHTTPRequest
  ) -> requests.ListChannelWebhooksHTTPResponse:
    response = await self._request_operation("list_channel_webhooks", request)
    if not isinstance(response, requests.ListChannelWebhooksHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_webhook(
    self, request: requests.CreateWebhookHTTPRequest
  ) -> requests.CreateWebhookHTTPResponse:
    response = await self._request_operation("create_webhook", request)
    if not isinstance(response, requests.CreateWebhookHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_gateway(
    self, request: requests.GetGatewayHTTPRequest
  ) -> requests.GetGatewayHTTPResponse:
    response = await self._request_operation("get_gateway", request)
    if not isinstance(response, requests.GetGatewayHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_bot_gateway(
    self, request: requests.GetBotGatewayHTTPRequest
  ) -> requests.GetBotGatewayHTTPResponse:
    response = await self._request_operation("get_bot_gateway", request)
    if not isinstance(response, requests.GetBotGatewayHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_template(
    self, request: requests.GetGuildTemplateHTTPRequest
  ) -> requests.GetGuildTemplateHTTPResponse:
    response = await self._request_operation("get_guild_template", request)
    if not isinstance(response, requests.GetGuildTemplateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild(
    self, request: requests.GetGuildHTTPRequest
  ) -> requests.GetGuildHTTPResponse:
    response = await self._request_operation("get_guild", request)
    if not isinstance(response, requests.GetGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild(
    self, request: requests.UpdateGuildHTTPRequest
  ) -> requests.UpdateGuildHTTPResponse:
    response = await self._request_operation("update_guild", request)
    if not isinstance(response, requests.UpdateGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_audit_log_entries(
    self, request: requests.ListGuildAuditLogEntriesHTTPRequest
  ) -> requests.ListGuildAuditLogEntriesHTTPResponse:
    response = await self._request_operation("list_guild_audit_log_entries", request)
    if not isinstance(response, requests.ListGuildAuditLogEntriesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_auto_moderation_rules(
    self, request: requests.ListAutoModerationRulesHTTPRequest
  ) -> requests.ListAutoModerationRulesHTTPResponse:
    response = await self._request_operation("list_auto_moderation_rules", request)
    if not isinstance(response, requests.ListAutoModerationRulesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_auto_moderation_rule(
    self, request: requests.CreateAutoModerationRuleHTTPRequest
  ) -> requests.CreateAutoModerationRuleHTTPResponse:
    response = await self._request_operation("create_auto_moderation_rule", request)
    if not isinstance(response, requests.CreateAutoModerationRuleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_auto_moderation_rule(
    self, request: requests.DeleteAutoModerationRuleHTTPRequest
  ) -> requests.DeleteAutoModerationRuleHTTPResponse:
    response = await self._request_operation("delete_auto_moderation_rule", request)
    if not isinstance(response, requests.DeleteAutoModerationRuleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_auto_moderation_rule(
    self, request: requests.GetAutoModerationRuleHTTPRequest
  ) -> requests.GetAutoModerationRuleHTTPResponse:
    response = await self._request_operation("get_auto_moderation_rule", request)
    if not isinstance(response, requests.GetAutoModerationRuleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_auto_moderation_rule(
    self, request: requests.UpdateAutoModerationRuleHTTPRequest
  ) -> requests.UpdateAutoModerationRuleHTTPResponse:
    response = await self._request_operation("update_auto_moderation_rule", request)
    if not isinstance(response, requests.UpdateAutoModerationRuleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_bans(
    self, request: requests.ListGuildBansHTTPRequest
  ) -> requests.ListGuildBansHTTPResponse:
    response = await self._request_operation("list_guild_bans", request)
    if not isinstance(response, requests.ListGuildBansHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def unban_user_from_guild(
    self, request: requests.UnbanUserFromGuildHTTPRequest
  ) -> requests.UnbanUserFromGuildHTTPResponse:
    response = await self._request_operation("unban_user_from_guild", request)
    if not isinstance(response, requests.UnbanUserFromGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_ban(
    self, request: requests.GetGuildBanHTTPRequest
  ) -> requests.GetGuildBanHTTPResponse:
    response = await self._request_operation("get_guild_ban", request)
    if not isinstance(response, requests.GetGuildBanHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def ban_user_from_guild(
    self, request: requests.BanUserFromGuildHTTPRequest
  ) -> requests.BanUserFromGuildHTTPResponse:
    response = await self._request_operation("ban_user_from_guild", request)
    if not isinstance(response, requests.BanUserFromGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bulk_ban_users_from_guild(
    self, request: requests.BulkBanUsersFromGuildHTTPRequest
  ) -> requests.BulkBanUsersFromGuildHTTPResponse:
    response = await self._request_operation("bulk_ban_users_from_guild", request)
    if not isinstance(response, requests.BulkBanUsersFromGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_channels(
    self, request: requests.ListGuildChannelsHTTPRequest
  ) -> requests.ListGuildChannelsHTTPResponse:
    response = await self._request_operation("list_guild_channels", request)
    if not isinstance(response, requests.ListGuildChannelsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bulk_update_guild_channels(
    self, request: requests.BulkUpdateGuildChannelsHTTPRequest
  ) -> requests.BulkUpdateGuildChannelsHTTPResponse:
    response = await self._request_operation("bulk_update_guild_channels", request)
    if not isinstance(response, requests.BulkUpdateGuildChannelsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_channel(
    self, request: requests.CreateGuildChannelHTTPRequest
  ) -> requests.CreateGuildChannelHTTPResponse:
    response = await self._request_operation("create_guild_channel", request)
    if not isinstance(response, requests.CreateGuildChannelHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_emojis(
    self, request: requests.ListGuildEmojisHTTPRequest
  ) -> requests.ListGuildEmojisHTTPResponse:
    response = await self._request_operation("list_guild_emojis", request)
    if not isinstance(response, requests.ListGuildEmojisHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_emoji(
    self, request: requests.CreateGuildEmojiHTTPRequest
  ) -> requests.CreateGuildEmojiHTTPResponse:
    response = await self._request_operation("create_guild_emoji", request)
    if not isinstance(response, requests.CreateGuildEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_emoji(
    self, request: requests.DeleteGuildEmojiHTTPRequest
  ) -> requests.DeleteGuildEmojiHTTPResponse:
    response = await self._request_operation("delete_guild_emoji", request)
    if not isinstance(response, requests.DeleteGuildEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_emoji(
    self, request: requests.GetGuildEmojiHTTPRequest
  ) -> requests.GetGuildEmojiHTTPResponse:
    response = await self._request_operation("get_guild_emoji", request)
    if not isinstance(response, requests.GetGuildEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_emoji(
    self, request: requests.UpdateGuildEmojiHTTPRequest
  ) -> requests.UpdateGuildEmojiHTTPResponse:
    response = await self._request_operation("update_guild_emoji", request)
    if not isinstance(response, requests.UpdateGuildEmojiHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_incident_actions(
    self, request: requests.UpdateGuildIncidentActionsHTTPRequest
  ) -> requests.UpdateGuildIncidentActionsHTTPResponse:
    response = await self._request_operation("update_guild_incident_actions", request)
    if not isinstance(response, requests.UpdateGuildIncidentActionsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_integrations(
    self, request: requests.ListGuildIntegrationsHTTPRequest
  ) -> requests.ListGuildIntegrationsHTTPResponse:
    response = await self._request_operation("list_guild_integrations", request)
    if not isinstance(response, requests.ListGuildIntegrationsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_integration(
    self, request: requests.DeleteGuildIntegrationHTTPRequest
  ) -> requests.DeleteGuildIntegrationHTTPResponse:
    response = await self._request_operation("delete_guild_integration", request)
    if not isinstance(response, requests.DeleteGuildIntegrationHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_invites(
    self, request: requests.ListGuildInvitesHTTPRequest
  ) -> requests.ListGuildInvitesHTTPResponse:
    response = await self._request_operation("list_guild_invites", request)
    if not isinstance(response, requests.ListGuildInvitesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_members(
    self, request: requests.ListGuildMembersHTTPRequest
  ) -> requests.ListGuildMembersHTTPResponse:
    response = await self._request_operation("list_guild_members", request)
    if not isinstance(response, requests.ListGuildMembersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_my_guild_member(
    self, request: requests.UpdateMyGuildMemberHTTPRequest
  ) -> requests.UpdateMyGuildMemberHTTPResponse:
    response = await self._request_operation("update_my_guild_member", request)
    if not isinstance(response, requests.UpdateMyGuildMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def search_guild_members(
    self, request: requests.SearchGuildMembersHTTPRequest
  ) -> requests.SearchGuildMembersHTTPResponse:
    response = await self._request_operation("search_guild_members", request)
    if not isinstance(response, requests.SearchGuildMembersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_member(
    self, request: requests.DeleteGuildMemberHTTPRequest
  ) -> requests.DeleteGuildMemberHTTPResponse:
    response = await self._request_operation("delete_guild_member", request)
    if not isinstance(response, requests.DeleteGuildMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_member(
    self, request: requests.GetGuildMemberHTTPRequest
  ) -> requests.GetGuildMemberHTTPResponse:
    response = await self._request_operation("get_guild_member", request)
    if not isinstance(response, requests.GetGuildMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_member(
    self, request: requests.UpdateGuildMemberHTTPRequest
  ) -> requests.UpdateGuildMemberHTTPResponse:
    response = await self._request_operation("update_guild_member", request)
    if not isinstance(response, requests.UpdateGuildMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def add_guild_member(
    self, request: requests.AddGuildMemberHTTPRequest
  ) -> requests.AddGuildMemberHTTPResponse:
    response = await self._request_operation("add_guild_member", request)
    if not isinstance(response, requests.AddGuildMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_member_role(
    self, request: requests.DeleteGuildMemberRoleHTTPRequest
  ) -> requests.DeleteGuildMemberRoleHTTPResponse:
    response = await self._request_operation("delete_guild_member_role", request)
    if not isinstance(response, requests.DeleteGuildMemberRoleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def add_guild_member_role(
    self, request: requests.AddGuildMemberRoleHTTPRequest
  ) -> requests.AddGuildMemberRoleHTTPResponse:
    response = await self._request_operation("add_guild_member_role", request)
    if not isinstance(response, requests.AddGuildMemberRoleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def guild_search(
    self, request: requests.GuildSearchHTTPRequest
  ) -> requests.GuildSearchHTTPResponse:
    response = await self._request_operation("guild_search", request)
    if not isinstance(response, requests.GuildSearchHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_new_member_welcome(
    self, request: requests.GetGuildNewMemberWelcomeHTTPRequest
  ) -> requests.GetGuildNewMemberWelcomeHTTPResponse:
    response = await self._request_operation("get_guild_new_member_welcome", request)
    if not isinstance(response, requests.GetGuildNewMemberWelcomeHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guilds_onboarding(
    self, request: requests.GetGuildsOnboardingHTTPRequest
  ) -> requests.GetGuildsOnboardingHTTPResponse:
    response = await self._request_operation("get_guilds_onboarding", request)
    if not isinstance(response, requests.GetGuildsOnboardingHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def put_guilds_onboarding(
    self, request: requests.PutGuildsOnboardingHTTPRequest
  ) -> requests.PutGuildsOnboardingHTTPResponse:
    response = await self._request_operation("put_guilds_onboarding", request)
    if not isinstance(response, requests.PutGuildsOnboardingHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_preview(
    self, request: requests.GetGuildPreviewHTTPRequest
  ) -> requests.GetGuildPreviewHTTPResponse:
    response = await self._request_operation("get_guild_preview", request)
    if not isinstance(response, requests.GetGuildPreviewHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def preview_prune_guild(
    self, request: requests.PreviewPruneGuildHTTPRequest
  ) -> requests.PreviewPruneGuildHTTPResponse:
    response = await self._request_operation("preview_prune_guild", request)
    if not isinstance(response, requests.PreviewPruneGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def prune_guild(
    self, request: requests.PruneGuildHTTPRequest
  ) -> requests.PruneGuildHTTPResponse:
    response = await self._request_operation("prune_guild", request)
    if not isinstance(response, requests.PruneGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_voice_regions(
    self, request: requests.ListGuildVoiceRegionsHTTPRequest
  ) -> requests.ListGuildVoiceRegionsHTTPResponse:
    response = await self._request_operation("list_guild_voice_regions", request)
    if not isinstance(response, requests.ListGuildVoiceRegionsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_join_requests(
    self, request: requests.GetGuildJoinRequestsHTTPRequest
  ) -> requests.GetGuildJoinRequestsHTTPResponse:
    response = await self._request_operation("get_guild_join_requests", request)
    if not isinstance(response, requests.GetGuildJoinRequestsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def action_guild_join_request(
    self, request: requests.ActionGuildJoinRequestHTTPRequest
  ) -> requests.ActionGuildJoinRequestHTTPResponse:
    response = await self._request_operation("action_guild_join_request", request)
    if not isinstance(response, requests.ActionGuildJoinRequestHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_roles(
    self, request: requests.ListGuildRolesHTTPRequest
  ) -> requests.ListGuildRolesHTTPResponse:
    response = await self._request_operation("list_guild_roles", request)
    if not isinstance(response, requests.ListGuildRolesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bulk_update_guild_roles(
    self, request: requests.BulkUpdateGuildRolesHTTPRequest
  ) -> requests.BulkUpdateGuildRolesHTTPResponse:
    response = await self._request_operation("bulk_update_guild_roles", request)
    if not isinstance(response, requests.BulkUpdateGuildRolesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_role(
    self, request: requests.CreateGuildRoleHTTPRequest
  ) -> requests.CreateGuildRoleHTTPResponse:
    response = await self._request_operation("create_guild_role", request)
    if not isinstance(response, requests.CreateGuildRoleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def guild_role_member_counts(
    self, request: requests.GuildRoleMemberCountsHTTPRequest
  ) -> requests.GuildRoleMemberCountsHTTPResponse:
    response = await self._request_operation("guild_role_member_counts", request)
    if not isinstance(response, requests.GuildRoleMemberCountsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_role(
    self, request: requests.DeleteGuildRoleHTTPRequest
  ) -> requests.DeleteGuildRoleHTTPResponse:
    response = await self._request_operation("delete_guild_role", request)
    if not isinstance(response, requests.DeleteGuildRoleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_role(
    self, request: requests.GetGuildRoleHTTPRequest
  ) -> requests.GetGuildRoleHTTPResponse:
    response = await self._request_operation("get_guild_role", request)
    if not isinstance(response, requests.GetGuildRoleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_role(
    self, request: requests.UpdateGuildRoleHTTPRequest
  ) -> requests.UpdateGuildRoleHTTPResponse:
    response = await self._request_operation("update_guild_role", request)
    if not isinstance(response, requests.UpdateGuildRoleHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_scheduled_events(
    self, request: requests.ListGuildScheduledEventsHTTPRequest
  ) -> requests.ListGuildScheduledEventsHTTPResponse:
    response = await self._request_operation("list_guild_scheduled_events", request)
    if not isinstance(response, requests.ListGuildScheduledEventsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_scheduled_event(
    self, request: requests.CreateGuildScheduledEventHTTPRequest
  ) -> requests.CreateGuildScheduledEventHTTPResponse:
    response = await self._request_operation("create_guild_scheduled_event", request)
    if not isinstance(response, requests.CreateGuildScheduledEventHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_scheduled_event(
    self, request: requests.DeleteGuildScheduledEventHTTPRequest
  ) -> requests.DeleteGuildScheduledEventHTTPResponse:
    response = await self._request_operation("delete_guild_scheduled_event", request)
    if not isinstance(response, requests.DeleteGuildScheduledEventHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_scheduled_event(
    self, request: requests.GetGuildScheduledEventHTTPRequest
  ) -> requests.GetGuildScheduledEventHTTPResponse:
    response = await self._request_operation("get_guild_scheduled_event", request)
    if not isinstance(response, requests.GetGuildScheduledEventHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_scheduled_event(
    self, request: requests.UpdateGuildScheduledEventHTTPRequest
  ) -> requests.UpdateGuildScheduledEventHTTPResponse:
    response = await self._request_operation("update_guild_scheduled_event", request)
    if not isinstance(response, requests.UpdateGuildScheduledEventHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_scheduled_event_exception(
    self, request: requests.CreateGuildScheduledEventExceptionHTTPRequest
  ) -> requests.CreateGuildScheduledEventExceptionHTTPResponse:
    response = await self._request_operation(
      "create_guild_scheduled_event_exception", request
    )
    if not isinstance(
      response, requests.CreateGuildScheduledEventExceptionHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_scheduled_event_exception(
    self, request: requests.DeleteGuildScheduledEventExceptionHTTPRequest
  ) -> requests.DeleteGuildScheduledEventExceptionHTTPResponse:
    response = await self._request_operation(
      "delete_guild_scheduled_event_exception", request
    )
    if not isinstance(
      response, requests.DeleteGuildScheduledEventExceptionHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_scheduled_event_exception(
    self, request: requests.UpdateGuildScheduledEventExceptionHTTPRequest
  ) -> requests.UpdateGuildScheduledEventExceptionHTTPResponse:
    response = await self._request_operation(
      "update_guild_scheduled_event_exception", request
    )
    if not isinstance(
      response, requests.UpdateGuildScheduledEventExceptionHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_scheduled_event_users(
    self, request: requests.ListGuildScheduledEventUsersHTTPRequest
  ) -> requests.ListGuildScheduledEventUsersHTTPResponse:
    response = await self._request_operation(
      "list_guild_scheduled_event_users", request
    )
    if not isinstance(response, requests.ListGuildScheduledEventUsersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def count_guild_scheduled_event_users(
    self, request: requests.CountGuildScheduledEventUsersHTTPRequest
  ) -> requests.CountGuildScheduledEventUsersHTTPResponse:
    response = await self._request_operation(
      "count_guild_scheduled_event_users", request
    )
    if not isinstance(response, requests.CountGuildScheduledEventUsersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_scheduled_event_exception_users(
    self, request: requests.ListGuildScheduledEventExceptionUsersHTTPRequest
  ) -> requests.ListGuildScheduledEventExceptionUsersHTTPResponse:
    response = await self._request_operation(
      "list_guild_scheduled_event_exception_users", request
    )
    if not isinstance(
      response, requests.ListGuildScheduledEventExceptionUsersHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_soundboard_sounds(
    self, request: requests.ListGuildSoundboardSoundsHTTPRequest
  ) -> requests.ListGuildSoundboardSoundsHTTPResponse:
    response = await self._request_operation("list_guild_soundboard_sounds", request)
    if not isinstance(response, requests.ListGuildSoundboardSoundsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_soundboard_sound(
    self, request: requests.CreateGuildSoundboardSoundHTTPRequest
  ) -> requests.CreateGuildSoundboardSoundHTTPResponse:
    response = await self._request_operation("create_guild_soundboard_sound", request)
    if not isinstance(response, requests.CreateGuildSoundboardSoundHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_soundboard_sound(
    self, request: requests.DeleteGuildSoundboardSoundHTTPRequest
  ) -> requests.DeleteGuildSoundboardSoundHTTPResponse:
    response = await self._request_operation("delete_guild_soundboard_sound", request)
    if not isinstance(response, requests.DeleteGuildSoundboardSoundHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_soundboard_sound(
    self, request: requests.GetGuildSoundboardSoundHTTPRequest
  ) -> requests.GetGuildSoundboardSoundHTTPResponse:
    response = await self._request_operation("get_guild_soundboard_sound", request)
    if not isinstance(response, requests.GetGuildSoundboardSoundHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_soundboard_sound(
    self, request: requests.UpdateGuildSoundboardSoundHTTPRequest
  ) -> requests.UpdateGuildSoundboardSoundHTTPResponse:
    response = await self._request_operation("update_guild_soundboard_sound", request)
    if not isinstance(response, requests.UpdateGuildSoundboardSoundHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_stickers(
    self, request: requests.ListGuildStickersHTTPRequest
  ) -> requests.ListGuildStickersHTTPResponse:
    response = await self._request_operation("list_guild_stickers", request)
    if not isinstance(response, requests.ListGuildStickersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_sticker(
    self, request: requests.CreateGuildStickerHTTPRequest
  ) -> requests.CreateGuildStickerHTTPResponse:
    response = await self._request_operation("create_guild_sticker", request)
    if not isinstance(response, requests.CreateGuildStickerHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_sticker(
    self, request: requests.DeleteGuildStickerHTTPRequest
  ) -> requests.DeleteGuildStickerHTTPResponse:
    response = await self._request_operation("delete_guild_sticker", request)
    if not isinstance(response, requests.DeleteGuildStickerHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_sticker(
    self, request: requests.GetGuildStickerHTTPRequest
  ) -> requests.GetGuildStickerHTTPResponse:
    response = await self._request_operation("get_guild_sticker", request)
    if not isinstance(response, requests.GetGuildStickerHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_sticker(
    self, request: requests.UpdateGuildStickerHTTPRequest
  ) -> requests.UpdateGuildStickerHTTPResponse:
    response = await self._request_operation("update_guild_sticker", request)
    if not isinstance(response, requests.UpdateGuildStickerHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_guild_templates(
    self, request: requests.ListGuildTemplatesHTTPRequest
  ) -> requests.ListGuildTemplatesHTTPResponse:
    response = await self._request_operation("list_guild_templates", request)
    if not isinstance(response, requests.ListGuildTemplatesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_guild_template(
    self, request: requests.CreateGuildTemplateHTTPRequest
  ) -> requests.CreateGuildTemplateHTTPResponse:
    response = await self._request_operation("create_guild_template", request)
    if not isinstance(response, requests.CreateGuildTemplateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_guild_template(
    self, request: requests.DeleteGuildTemplateHTTPRequest
  ) -> requests.DeleteGuildTemplateHTTPResponse:
    response = await self._request_operation("delete_guild_template", request)
    if not isinstance(response, requests.DeleteGuildTemplateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_template(
    self, request: requests.UpdateGuildTemplateHTTPRequest
  ) -> requests.UpdateGuildTemplateHTTPResponse:
    response = await self._request_operation("update_guild_template", request)
    if not isinstance(response, requests.UpdateGuildTemplateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def sync_guild_template(
    self, request: requests.SyncGuildTemplateHTTPRequest
  ) -> requests.SyncGuildTemplateHTTPResponse:
    response = await self._request_operation("sync_guild_template", request)
    if not isinstance(response, requests.SyncGuildTemplateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_active_guild_threads(
    self, request: requests.GetActiveGuildThreadsHTTPRequest
  ) -> requests.GetActiveGuildThreadsHTTPResponse:
    response = await self._request_operation("get_active_guild_threads", request)
    if not isinstance(response, requests.GetActiveGuildThreadsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_vanity_url(
    self, request: requests.GetGuildVanityUrlHTTPRequest
  ) -> requests.GetGuildVanityUrlHTTPResponse:
    response = await self._request_operation("get_guild_vanity_url", request)
    if not isinstance(response, requests.GetGuildVanityUrlHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_self_voice_state(
    self, request: requests.GetSelfVoiceStateHTTPRequest
  ) -> requests.GetSelfVoiceStateHTTPResponse:
    response = await self._request_operation("get_self_voice_state", request)
    if not isinstance(response, requests.GetSelfVoiceStateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_self_voice_state(
    self, request: requests.UpdateSelfVoiceStateHTTPRequest
  ) -> requests.UpdateSelfVoiceStateHTTPResponse:
    response = await self._request_operation("update_self_voice_state", request)
    if not isinstance(response, requests.UpdateSelfVoiceStateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_voice_state(
    self, request: requests.GetVoiceStateHTTPRequest
  ) -> requests.GetVoiceStateHTTPResponse:
    response = await self._request_operation("get_voice_state", request)
    if not isinstance(response, requests.GetVoiceStateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_voice_state(
    self, request: requests.UpdateVoiceStateHTTPRequest
  ) -> requests.UpdateVoiceStateHTTPResponse:
    response = await self._request_operation("update_voice_state", request)
    if not isinstance(response, requests.UpdateVoiceStateHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_webhooks(
    self, request: requests.GetGuildWebhooksHTTPRequest
  ) -> requests.GetGuildWebhooksHTTPResponse:
    response = await self._request_operation("get_guild_webhooks", request)
    if not isinstance(response, requests.GetGuildWebhooksHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_welcome_screen(
    self, request: requests.GetGuildWelcomeScreenHTTPRequest
  ) -> requests.GetGuildWelcomeScreenHTTPResponse:
    response = await self._request_operation("get_guild_welcome_screen", request)
    if not isinstance(response, requests.GetGuildWelcomeScreenHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_welcome_screen(
    self, request: requests.UpdateGuildWelcomeScreenHTTPRequest
  ) -> requests.UpdateGuildWelcomeScreenHTTPResponse:
    response = await self._request_operation("update_guild_welcome_screen", request)
    if not isinstance(response, requests.UpdateGuildWelcomeScreenHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_widget_settings(
    self, request: requests.GetGuildWidgetSettingsHTTPRequest
  ) -> requests.GetGuildWidgetSettingsHTTPResponse:
    response = await self._request_operation("get_guild_widget_settings", request)
    if not isinstance(response, requests.GetGuildWidgetSettingsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_guild_widget_settings(
    self, request: requests.UpdateGuildWidgetSettingsHTTPRequest
  ) -> requests.UpdateGuildWidgetSettingsHTTPResponse:
    response = await self._request_operation("update_guild_widget_settings", request)
    if not isinstance(response, requests.UpdateGuildWidgetSettingsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_widget(
    self, request: requests.GetGuildWidgetHTTPRequest
  ) -> requests.GetGuildWidgetHTTPResponse:
    response = await self._request_operation("get_guild_widget", request)
    if not isinstance(response, requests.GetGuildWidgetHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_guild_widget_png(
    self, request: requests.GetGuildWidgetPngHTTPRequest
  ) -> requests.GetGuildWidgetPngHTTPResponse:
    response = await self._request_operation("get_guild_widget_png", request)
    if not isinstance(response, requests.GetGuildWidgetPngHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_interaction_response(
    self, request: requests.CreateInteractionResponseHTTPRequest
  ) -> requests.CreateInteractionResponseHTTPResponse:
    response = await self._request_operation("create_interaction_response", request)
    if not isinstance(response, requests.CreateInteractionResponseHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def invite_revoke(
    self, request: requests.InviteRevokeHTTPRequest
  ) -> requests.InviteRevokeHTTPResponse:
    response = await self._request_operation("invite_revoke", request)
    if not isinstance(response, requests.InviteRevokeHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def invite_resolve(
    self, request: requests.InviteResolveHTTPRequest
  ) -> requests.InviteResolveHTTPResponse:
    response = await self._request_operation("invite_resolve", request)
    if not isinstance(response, requests.InviteResolveHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_invite_target_users(
    self, request: requests.GetInviteTargetUsersHTTPRequest
  ) -> requests.GetInviteTargetUsersHTTPResponse:
    response = await self._request_operation("get_invite_target_users", request)
    if not isinstance(response, requests.GetInviteTargetUsersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_invite_target_users(
    self, request: requests.UpdateInviteTargetUsersHTTPRequest
  ) -> requests.UpdateInviteTargetUsersHTTPResponse:
    response = await self._request_operation("update_invite_target_users", request)
    if not isinstance(response, requests.UpdateInviteTargetUsersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_invite_target_users_job_status(
    self, request: requests.GetInviteTargetUsersJobStatusHTTPRequest
  ) -> requests.GetInviteTargetUsersJobStatusHTTPResponse:
    response = await self._request_operation(
      "get_invite_target_users_job_status", request
    )
    if not isinstance(response, requests.GetInviteTargetUsersJobStatusHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_lobby(
    self, request: requests.CreateLobbyHTTPRequest
  ) -> requests.CreateLobbyHTTPResponse:
    response = await self._request_operation("create_lobby", request)
    if not isinstance(response, requests.CreateLobbyHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_or_join_lobby(
    self, request: requests.CreateOrJoinLobbyHTTPRequest
  ) -> requests.CreateOrJoinLobbyHTTPResponse:
    response = await self._request_operation("create_or_join_lobby", request)
    if not isinstance(response, requests.CreateOrJoinLobbyHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_lobby(
    self, request: requests.DeleteLobbyHTTPRequest
  ) -> requests.DeleteLobbyHTTPResponse:
    response = await self._request_operation("delete_lobby", request)
    if not isinstance(response, requests.DeleteLobbyHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_lobby(
    self, request: requests.GetLobbyHTTPRequest
  ) -> requests.GetLobbyHTTPResponse:
    response = await self._request_operation("get_lobby", request)
    if not isinstance(response, requests.GetLobbyHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def edit_lobby(
    self, request: requests.EditLobbyHTTPRequest
  ) -> requests.EditLobbyHTTPResponse:
    response = await self._request_operation("edit_lobby", request)
    if not isinstance(response, requests.EditLobbyHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def edit_lobby_channel_link(
    self, request: requests.EditLobbyChannelLinkHTTPRequest
  ) -> requests.EditLobbyChannelLinkHTTPResponse:
    response = await self._request_operation("edit_lobby_channel_link", request)
    if not isinstance(response, requests.EditLobbyChannelLinkHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def leave_lobby(
    self, request: requests.LeaveLobbyHTTPRequest
  ) -> requests.LeaveLobbyHTTPResponse:
    response = await self._request_operation("leave_lobby", request)
    if not isinstance(response, requests.LeaveLobbyHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_linked_lobby_guild_invite_for_self(
    self, request: requests.CreateLinkedLobbyGuildInviteForSelfHTTPRequest
  ) -> requests.CreateLinkedLobbyGuildInviteForSelfHTTPResponse:
    response = await self._request_operation(
      "create_linked_lobby_guild_invite_for_self", request
    )
    if not isinstance(
      response, requests.CreateLinkedLobbyGuildInviteForSelfHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bulk_update_lobby_members(
    self, request: requests.BulkUpdateLobbyMembersHTTPRequest
  ) -> requests.BulkUpdateLobbyMembersHTTPResponse:
    response = await self._request_operation("bulk_update_lobby_members", request)
    if not isinstance(response, requests.BulkUpdateLobbyMembersHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_lobby_member(
    self, request: requests.DeleteLobbyMemberHTTPRequest
  ) -> requests.DeleteLobbyMemberHTTPResponse:
    response = await self._request_operation("delete_lobby_member", request)
    if not isinstance(response, requests.DeleteLobbyMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def add_lobby_member(
    self, request: requests.AddLobbyMemberHTTPRequest
  ) -> requests.AddLobbyMemberHTTPResponse:
    response = await self._request_operation("add_lobby_member", request)
    if not isinstance(response, requests.AddLobbyMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_linked_lobby_guild_invite_for_user(
    self, request: requests.CreateLinkedLobbyGuildInviteForUserHTTPRequest
  ) -> requests.CreateLinkedLobbyGuildInviteForUserHTTPResponse:
    response = await self._request_operation(
      "create_linked_lobby_guild_invite_for_user", request
    )
    if not isinstance(
      response, requests.CreateLinkedLobbyGuildInviteForUserHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_lobby_messages(
    self, request: requests.GetLobbyMessagesHTTPRequest
  ) -> requests.GetLobbyMessagesHTTPResponse:
    response = await self._request_operation("get_lobby_messages", request)
    if not isinstance(response, requests.GetLobbyMessagesHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_lobby_message(
    self, request: requests.CreateLobbyMessageHTTPRequest
  ) -> requests.CreateLobbyMessageHTTPResponse:
    response = await self._request_operation("create_lobby_message", request)
    if not isinstance(response, requests.CreateLobbyMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_lobby_message_external_moderation_metadata(
    self, request: requests.UpdateLobbyMessageExternalModerationMetadataHTTPRequest
  ) -> requests.UpdateLobbyMessageExternalModerationMetadataHTTPResponse:
    response = await self._request_operation(
      "update_lobby_message_external_moderation_metadata", request
    )
    if not isinstance(
      response, requests.UpdateLobbyMessageExternalModerationMetadataHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_my_oauth2_authorization(
    self, request: requests.GetMyOauth2AuthorizationHTTPRequest
  ) -> requests.GetMyOauth2AuthorizationHTTPResponse:
    response = await self._request_operation("get_my_oauth2_authorization", request)
    if not isinstance(response, requests.GetMyOauth2AuthorizationHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_my_oauth2_application(
    self, request: requests.GetMyOauth2ApplicationHTTPRequest
  ) -> requests.GetMyOauth2ApplicationHTTPResponse:
    response = await self._request_operation("get_my_oauth2_application", request)
    if not isinstance(response, requests.GetMyOauth2ApplicationHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_public_keys(
    self, request: requests.GetPublicKeysHTTPRequest
  ) -> requests.GetPublicKeysHTTPResponse:
    response = await self._request_operation("get_public_keys", request)
    if not isinstance(response, requests.GetPublicKeysHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_openid_connect_userinfo(
    self, request: requests.GetOpenidConnectUserinfoHTTPRequest
  ) -> requests.GetOpenidConnectUserinfoHTTPResponse:
    response = await self._request_operation("get_openid_connect_userinfo", request)
    if not isinstance(response, requests.GetOpenidConnectUserinfoHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_user_message_external_moderation_metadata(
    self, request: requests.UpdateUserMessageExternalModerationMetadataHTTPRequest
  ) -> requests.UpdateUserMessageExternalModerationMetadataHTTPResponse:
    response = await self._request_operation(
      "update_user_message_external_moderation_metadata", request
    )
    if not isinstance(
      response, requests.UpdateUserMessageExternalModerationMetadataHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def partner_sdk_unmerge_provisional_account(
    self, request: requests.PartnerSdkUnmergeProvisionalAccountHTTPRequest
  ) -> requests.PartnerSdkUnmergeProvisionalAccountHTTPResponse:
    response = await self._request_operation(
      "partner_sdk_unmerge_provisional_account", request
    )
    if not isinstance(
      response, requests.PartnerSdkUnmergeProvisionalAccountHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bot_partner_sdk_unmerge_provisional_account(
    self, request: requests.BotPartnerSdkUnmergeProvisionalAccountHTTPRequest
  ) -> requests.BotPartnerSdkUnmergeProvisionalAccountHTTPResponse:
    response = await self._request_operation(
      "bot_partner_sdk_unmerge_provisional_account", request
    )
    if not isinstance(
      response, requests.BotPartnerSdkUnmergeProvisionalAccountHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def partner_sdk_token(
    self, request: requests.PartnerSdkTokenHTTPRequest
  ) -> requests.PartnerSdkTokenHTTPResponse:
    response = await self._request_operation("partner_sdk_token", request)
    if not isinstance(response, requests.PartnerSdkTokenHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def bot_partner_sdk_token(
    self, request: requests.BotPartnerSdkTokenHTTPRequest
  ) -> requests.BotPartnerSdkTokenHTTPResponse:
    response = await self._request_operation("bot_partner_sdk_token", request)
    if not isinstance(response, requests.BotPartnerSdkTokenHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_sku_subscriptions(
    self, request: requests.GetSkuSubscriptionsHTTPRequest
  ) -> requests.GetSkuSubscriptionsHTTPResponse:
    response = await self._request_operation("get_sku_subscriptions", request)
    if not isinstance(response, requests.GetSkuSubscriptionsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_sku_subscription(
    self, request: requests.GetSkuSubscriptionHTTPRequest
  ) -> requests.GetSkuSubscriptionHTTPResponse:
    response = await self._request_operation("get_sku_subscription", request)
    if not isinstance(response, requests.GetSkuSubscriptionHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_soundboard_default_sounds(
    self, request: requests.GetSoundboardDefaultSoundsHTTPRequest
  ) -> requests.GetSoundboardDefaultSoundsHTTPResponse:
    response = await self._request_operation("get_soundboard_default_sounds", request)
    if not isinstance(response, requests.GetSoundboardDefaultSoundsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_stage_instance(
    self, request: requests.CreateStageInstanceHTTPRequest
  ) -> requests.CreateStageInstanceHTTPResponse:
    response = await self._request_operation("create_stage_instance", request)
    if not isinstance(response, requests.CreateStageInstanceHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_stage_instance(
    self, request: requests.DeleteStageInstanceHTTPRequest
  ) -> requests.DeleteStageInstanceHTTPResponse:
    response = await self._request_operation("delete_stage_instance", request)
    if not isinstance(response, requests.DeleteStageInstanceHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_stage_instance(
    self, request: requests.GetStageInstanceHTTPRequest
  ) -> requests.GetStageInstanceHTTPResponse:
    response = await self._request_operation("get_stage_instance", request)
    if not isinstance(response, requests.GetStageInstanceHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_stage_instance(
    self, request: requests.UpdateStageInstanceHTTPRequest
  ) -> requests.UpdateStageInstanceHTTPResponse:
    response = await self._request_operation("update_stage_instance", request)
    if not isinstance(response, requests.UpdateStageInstanceHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_sticker_packs(
    self, request: requests.ListStickerPacksHTTPRequest
  ) -> requests.ListStickerPacksHTTPResponse:
    response = await self._request_operation("list_sticker_packs", request)
    if not isinstance(response, requests.ListStickerPacksHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_sticker_pack(
    self, request: requests.GetStickerPackHTTPRequest
  ) -> requests.GetStickerPackHTTPResponse:
    response = await self._request_operation("get_sticker_pack", request)
    if not isinstance(response, requests.GetStickerPackHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_sticker(
    self, request: requests.GetStickerHTTPRequest
  ) -> requests.GetStickerHTTPResponse:
    response = await self._request_operation("get_sticker", request)
    if not isinstance(response, requests.GetStickerHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_my_user(
    self, request: requests.GetMyUserHTTPRequest
  ) -> requests.GetMyUserHTTPResponse:
    response = await self._request_operation("get_my_user", request)
    if not isinstance(response, requests.GetMyUserHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_my_user(
    self, request: requests.UpdateMyUserHTTPRequest
  ) -> requests.UpdateMyUserHTTPResponse:
    response = await self._request_operation("update_my_user", request)
    if not isinstance(response, requests.UpdateMyUserHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_current_user_application_entitlements(
    self, request: requests.GetCurrentUserApplicationEntitlementsHTTPRequest
  ) -> requests.GetCurrentUserApplicationEntitlementsHTTPResponse:
    response = await self._request_operation(
      "get_current_user_application_entitlements", request
    )
    if not isinstance(
      response, requests.GetCurrentUserApplicationEntitlementsHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_application_user_role_connection(
    self, request: requests.DeleteApplicationUserRoleConnectionHTTPRequest
  ) -> requests.DeleteApplicationUserRoleConnectionHTTPResponse:
    response = await self._request_operation(
      "delete_application_user_role_connection", request
    )
    if not isinstance(
      response, requests.DeleteApplicationUserRoleConnectionHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_application_user_role_connection(
    self, request: requests.GetApplicationUserRoleConnectionHTTPRequest
  ) -> requests.GetApplicationUserRoleConnectionHTTPResponse:
    response = await self._request_operation(
      "get_application_user_role_connection", request
    )
    if not isinstance(response, requests.GetApplicationUserRoleConnectionHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_application_user_role_connection(
    self, request: requests.UpdateApplicationUserRoleConnectionHTTPRequest
  ) -> requests.UpdateApplicationUserRoleConnectionHTTPResponse:
    response = await self._request_operation(
      "update_application_user_role_connection", request
    )
    if not isinstance(
      response, requests.UpdateApplicationUserRoleConnectionHTTPResponse
    ):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def create_dm(
    self, request: requests.CreateDmHTTPRequest
  ) -> requests.CreateDmHTTPResponse:
    response = await self._request_operation("create_dm", request)
    if not isinstance(response, requests.CreateDmHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_my_connections(
    self, request: requests.ListMyConnectionsHTTPRequest
  ) -> requests.ListMyConnectionsHTTPResponse:
    response = await self._request_operation("list_my_connections", request)
    if not isinstance(response, requests.ListMyConnectionsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_my_guilds(
    self, request: requests.ListMyGuildsHTTPRequest
  ) -> requests.ListMyGuildsHTTPResponse:
    response = await self._request_operation("list_my_guilds", request)
    if not isinstance(response, requests.ListMyGuildsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def leave_guild(
    self, request: requests.LeaveGuildHTTPRequest
  ) -> requests.LeaveGuildHTTPResponse:
    response = await self._request_operation("leave_guild", request)
    if not isinstance(response, requests.LeaveGuildHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_my_guild_member(
    self, request: requests.GetMyGuildMemberHTTPRequest
  ) -> requests.GetMyGuildMemberHTTPResponse:
    response = await self._request_operation("get_my_guild_member", request)
    if not isinstance(response, requests.GetMyGuildMemberHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_user(
    self, request: requests.GetUserHTTPRequest
  ) -> requests.GetUserHTTPResponse:
    response = await self._request_operation("get_user", request)
    if not isinstance(response, requests.GetUserHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def list_voice_regions(
    self, request: requests.ListVoiceRegionsHTTPRequest
  ) -> requests.ListVoiceRegionsHTTPResponse:
    response = await self._request_operation("list_voice_regions", request)
    if not isinstance(response, requests.ListVoiceRegionsHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_webhook(
    self, request: requests.DeleteWebhookHTTPRequest
  ) -> requests.DeleteWebhookHTTPResponse:
    response = await self._request_operation("delete_webhook", request)
    if not isinstance(response, requests.DeleteWebhookHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_webhook(
    self, request: requests.GetWebhookHTTPRequest
  ) -> requests.GetWebhookHTTPResponse:
    response = await self._request_operation("get_webhook", request)
    if not isinstance(response, requests.GetWebhookHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_webhook(
    self, request: requests.UpdateWebhookHTTPRequest
  ) -> requests.UpdateWebhookHTTPResponse:
    response = await self._request_operation("update_webhook", request)
    if not isinstance(response, requests.UpdateWebhookHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_webhook_by_token(
    self, request: requests.DeleteWebhookByTokenHTTPRequest
  ) -> requests.DeleteWebhookByTokenHTTPResponse:
    response = await self._request_operation("delete_webhook_by_token", request)
    if not isinstance(response, requests.DeleteWebhookByTokenHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_webhook_by_token(
    self, request: requests.GetWebhookByTokenHTTPRequest
  ) -> requests.GetWebhookByTokenHTTPResponse:
    response = await self._request_operation("get_webhook_by_token", request)
    if not isinstance(response, requests.GetWebhookByTokenHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_webhook_by_token(
    self, request: requests.UpdateWebhookByTokenHTTPRequest
  ) -> requests.UpdateWebhookByTokenHTTPResponse:
    response = await self._request_operation("update_webhook_by_token", request)
    if not isinstance(response, requests.UpdateWebhookByTokenHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def execute_webhook(
    self, request: requests.ExecuteWebhookHTTPRequest
  ) -> requests.ExecuteWebhookHTTPResponse:
    response = await self._request_operation("execute_webhook", request)
    if not isinstance(response, requests.ExecuteWebhookHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def execute_github_compatible_webhook(
    self, request: requests.ExecuteGithubCompatibleWebhookHTTPRequest
  ) -> requests.ExecuteGithubCompatibleWebhookHTTPResponse:
    response = await self._request_operation(
      "execute_github_compatible_webhook", request
    )
    if not isinstance(response, requests.ExecuteGithubCompatibleWebhookHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_original_webhook_message(
    self, request: requests.DeleteOriginalWebhookMessageHTTPRequest
  ) -> requests.DeleteOriginalWebhookMessageHTTPResponse:
    response = await self._request_operation("delete_original_webhook_message", request)
    if not isinstance(response, requests.DeleteOriginalWebhookMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_original_webhook_message(
    self, request: requests.GetOriginalWebhookMessageHTTPRequest
  ) -> requests.GetOriginalWebhookMessageHTTPResponse:
    response = await self._request_operation("get_original_webhook_message", request)
    if not isinstance(response, requests.GetOriginalWebhookMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_original_webhook_message(
    self, request: requests.UpdateOriginalWebhookMessageHTTPRequest
  ) -> requests.UpdateOriginalWebhookMessageHTTPResponse:
    response = await self._request_operation("update_original_webhook_message", request)
    if not isinstance(response, requests.UpdateOriginalWebhookMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def delete_webhook_message(
    self, request: requests.DeleteWebhookMessageHTTPRequest
  ) -> requests.DeleteWebhookMessageHTTPResponse:
    response = await self._request_operation("delete_webhook_message", request)
    if not isinstance(response, requests.DeleteWebhookMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def get_webhook_message(
    self, request: requests.GetWebhookMessageHTTPRequest
  ) -> requests.GetWebhookMessageHTTPResponse:
    response = await self._request_operation("get_webhook_message", request)
    if not isinstance(response, requests.GetWebhookMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def update_webhook_message(
    self, request: requests.UpdateWebhookMessageHTTPRequest
  ) -> requests.UpdateWebhookMessageHTTPResponse:
    response = await self._request_operation("update_webhook_message", request)
    if not isinstance(response, requests.UpdateWebhookMessageHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response

  async def execute_slack_compatible_webhook(
    self, request: requests.ExecuteSlackCompatibleWebhookHTTPRequest
  ) -> requests.ExecuteSlackCompatibleWebhookHTTPResponse:
    response = await self._request_operation(
      "execute_slack_compatible_webhook", request
    )
    if not isinstance(response, requests.ExecuteSlackCompatibleWebhookHTTPResponse):
      raise TypeError("Discord HTTP transport returned the wrong response model.")
    return response


__all__ = (
  "HTTP_OPERATIONS",
  "DiscordHTTPOperation",
  "DiscordOperationId",
  "GeneratedDiscordHTTPClient",
)
