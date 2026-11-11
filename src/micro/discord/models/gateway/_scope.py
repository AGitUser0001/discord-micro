# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class Scope(StrEnum):
    activities_read = 'activities.read'
    activities_write = 'activities.write'
    applications_builds_read = 'applications.builds.read'
    applications_builds_upload = 'applications.builds.upload'
    applications_commands = 'applications.commands'
    applications_commands_permissions_update = (
        'applications.commands.permissions.update'
    )
    applications_commands_update = 'applications.commands.update'
    applications_entitlements = 'applications.entitlements'
    applications_store_update = 'applications.store.update'
    bot = 'bot'
    connections = 'connections'
    dm_channels_read = 'dm_channels.read'
    email = 'email'
    gdm_join = 'gdm.join'
    guilds = 'guilds'
    guilds_join = 'guilds.join'
    guilds_members_read = 'guilds.members.read'
    identify = 'identify'
    identify_premium = 'identify.premium'
    messages_read = 'messages.read'
    relationships_read = 'relationships.read'
    role_connections_write = 'role_connections.write'
    rpc = 'rpc'
    rpc_activities_write = 'rpc.activities.write'
    rpc_notifications_read = 'rpc.notifications.read'
    rpc_voice_read = 'rpc.voice.read'
    rpc_voice_write = 'rpc.voice.write'
    voice = 'voice'
    webhook_incoming = 'webhook.incoming'
