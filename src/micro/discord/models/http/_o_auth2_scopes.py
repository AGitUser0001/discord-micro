# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class OAuth2Scopes(StrEnum):
    IDENTIFY = 'identify'
    EMAIL = 'email'
    CONNECTIONS = 'connections'
    GUILDS = 'guilds'
    GUILDS_JOIN = 'guilds.join'
    GUILDS_MEMBERS_READ = 'guilds.members.read'
    GDM_JOIN = 'gdm.join'
    BOT = 'bot'
    RPC = 'rpc'
    RPC_NOTIFICATIONS_READ = 'rpc.notifications.read'
    RPC_VOICE_READ = 'rpc.voice.read'
    RPC_VOICE_WRITE = 'rpc.voice.write'
    RPC_VIDEO_READ = 'rpc.video.read'
    RPC_VIDEO_WRITE = 'rpc.video.write'
    RPC_SCREENSHARE_READ = 'rpc.screenshare.read'
    RPC_SCREENSHARE_WRITE = 'rpc.screenshare.write'
    RPC_ACTIVITIES_WRITE = 'rpc.activities.write'
    WEBHOOK_INCOMING = 'webhook.incoming'
    MESSAGES_READ = 'messages.read'
    APPLICATIONS_BUILDS_UPLOAD = 'applications.builds.upload'
    APPLICATIONS_BUILDS_READ = 'applications.builds.read'
    APPLICATIONS_COMMANDS = 'applications.commands'
    APPLICATIONS_COMMANDS_PERMISSIONS_UPDATE = (
        'applications.commands.permissions.update'
    )
    APPLICATIONS_COMMANDS_UPDATE = 'applications.commands.update'
    APPLICATIONS_STORE_UPDATE = 'applications.store.update'
    APPLICATIONS_ENTITLEMENTS = 'applications.entitlements'
    ACTIVITIES_READ = 'activities.read'
    ACTIVITIES_WRITE = 'activities.write'
    ACTIVITIES_INVITES_WRITE = 'activities.invites.write'
    RELATIONSHIPS_READ = 'relationships.read'
    VOICE = 'voice'
    DM_CHANNELS_READ = 'dm_channels.read'
    ROLE_CONNECTIONS_WRITE = 'role_connections.write'
    OPENID = 'openid'
