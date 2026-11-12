"""Discord for bots: everything you use, in one namespace.

    from micro.discord import Button, Draft, Embed, Interaction, Member, NotFound, Ok, Result

Components and messages (`Button`, `Draft`, `Embed`, ...), the objects Discord sends (`User`,
`Member`, `Guild`, ...), the enums (`ButtonStyle`, `ChannelType`, ...), `Asset`, `Colour`,
`Permissions`, the interaction handlers (`Interaction`, `Commands`, ...), `DiscordState`, the
errors (`NotFound`, `Forbidden`, ...) and `Ok`/`Err`/`Result` are all here, so one import finds
them. Less common things stay in their module: `filters`, `text`, `invite`, `routes`, and the
worker's internals in `http_service`. The names are loaded when first used.
"""

from typing import TYPE_CHECKING

from micro._lazy import exports

if TYPE_CHECKING:
  from micro.discord import asset as asset
  from micro.discord import colour as colour
  from micro.discord import enums as enums
  from micro.discord import filters as filters
  from micro.discord import http_operations as http_operations
  from micro.discord import http_service as http_service
  from micro.discord import interactions as interactions
  from micro.discord import invite as invite
  from micro.discord import models as models
  from micro.discord import objects as objects
  from micro.discord import permissions as permissions
  from micro.discord import routes as routes
  from micro.discord import state as state
  from micro.discord import text as text
  from micro.discord import ui as ui
  from micro.discord.asset import Asset as Asset
  from micro.discord.colour import Colour as Colour
  from micro.discord.colour import ColourLike as ColourLike
  from micro.discord.enums import ButtonStyle as ButtonStyle
  from micro.discord.enums import ChannelType as ChannelType
  from micro.discord.enums import CommandType as CommandType
  from micro.discord.enums import InteractionType as InteractionType
  from micro.discord.enums import OverwriteType as OverwriteType
  from micro.discord.enums import TextInputStyle as TextInputStyle
  from micro.discord.files import DownloadError as DownloadError
  from micro.discord.files import download as download
  from micro.discord.http_service import BadRequest as BadRequest
  from micro.discord.http_service import DiscordAPIError as DiscordAPIError
  from micro.discord.http_service import DiscordHTTPClient as DiscordHTTPClient
  from micro.discord.http_service import DiscordHTTPWorker as DiscordHTTPWorker
  from micro.discord.http_service import DiscordServerError as DiscordServerError
  from micro.discord.http_service import Forbidden as Forbidden
  from micro.discord.http_service import NotFound as NotFound
  from micro.discord.http_service import RateLimited as RateLimited
  from micro.discord.http_service import Unauthorized as Unauthorized
  from micro.discord.interactions import Choice as Choice
  from micro.discord.interactions import Commands as Commands
  from micro.discord.interactions import Components as Components
  from micro.discord.interactions import Context as Context
  from micro.discord.interactions import CustomId as CustomId
  from micro.discord.interactions import Interaction as Interaction
  from micro.discord.interactions import Modals as Modals
  from micro.discord.interactions import Option as Option
  from micro.discord.objects import Attachment as Attachment
  from micro.discord.objects import Channel as Channel
  from micro.discord.objects import Guild as Guild
  from micro.discord.objects import GuildEmoji as GuildEmoji
  from micro.discord.objects import Member as Member
  from micro.discord.objects import Message as Message
  from micro.discord.objects import Object as Object
  from micro.discord.objects import PermissionOverwrite as PermissionOverwrite
  from micro.discord.objects import Presence as Presence
  from micro.discord.objects import Role as Role
  from micro.discord.objects import ScheduledEvent as ScheduledEvent
  from micro.discord.objects import StageInstance as StageInstance
  from micro.discord.objects import Sticker as Sticker
  from micro.discord.objects import User as User
  from micro.discord.objects import VoiceState as VoiceState
  from micro.discord.permissions import Permissions as Permissions
  from micro.discord.state import DiscordState as DiscordState
  from micro.discord.state import KnownGuild as KnownGuild
  from micro.discord.ui import ActionRow as ActionRow
  from micro.discord.ui import AllowedMentions as AllowedMentions
  from micro.discord.ui import Button as Button
  from micro.discord.ui import ChannelSelect as ChannelSelect
  from micro.discord.ui import Checkbox as Checkbox
  from micro.discord.ui import CheckboxGroup as CheckboxGroup
  from micro.discord.ui import Component as Component
  from micro.discord.ui import Container as Container
  from micro.discord.ui import Default as Default
  from micro.discord.ui import Draft as Draft
  from micro.discord.ui import Embed as Embed
  from micro.discord.ui import EmbedAuthor as EmbedAuthor
  from micro.discord.ui import EmbedField as EmbedField
  from micro.discord.ui import EmbedFooter as EmbedFooter
  from micro.discord.ui import Emoji as Emoji
  from micro.discord.ui import File as File
  from micro.discord.ui import FileUpload as FileUpload
  from micro.discord.ui import GroupOption as GroupOption
  from micro.discord.ui import Label as Label
  from micro.discord.ui import MediaGallery as MediaGallery
  from micro.discord.ui import MediaItem as MediaItem
  from micro.discord.ui import MentionableSelect as MentionableSelect
  from micro.discord.ui import Modal as Modal
  from micro.discord.ui import RadioGroup as RadioGroup
  from micro.discord.ui import RoleSelect as RoleSelect
  from micro.discord.ui import Section as Section
  from micro.discord.ui import SelectOption as SelectOption
  from micro.discord.ui import Separator as Separator
  from micro.discord.ui import StringSelect as StringSelect
  from micro.discord.ui import TextDisplay as TextDisplay
  from micro.discord.ui import TextInput as TextInput
  from micro.discord.ui import Thumbnail as Thumbnail
  from micro.discord.ui import Upload as Upload
  from micro.discord.ui import UserSelect as UserSelect
  from micro.result import Err as Err
  from micro.result import Ok as Ok
  from micro.result import Result as Result

__getattr__, __dir__ = exports(
  __name__,
  {
    "asset": ".asset",
    "colour": ".colour",
    "enums": ".enums",
    "filters": ".filters",
    "http_operations": ".http_operations",
    "http_service": ".http_service",
    "interactions": ".interactions",
    "invite": ".invite",
    "models": ".models",
    "objects": ".objects",
    "permissions": ".permissions",
    "routes": ".routes",
    "state": ".state",
    "text": ".text",
    "ui": ".ui",
    "ActionRow": ".ui",
    "AllowedMentions": ".ui",
    "Asset": ".asset",
    "Attachment": ".objects",
    "VoiceState": ".objects",
    "Sticker": ".objects",
    "StageInstance": ".objects",
    "ScheduledEvent": ".objects",
    "Presence": ".objects",
    "GuildEmoji": ".objects",
    "BadRequest": ".http_service",
    "Button": ".ui",
    "ButtonStyle": ".enums",
    "Channel": ".objects",
    "ChannelSelect": ".ui",
    "ChannelType": ".enums",
    "Checkbox": ".ui",
    "CheckboxGroup": ".ui",
    "Choice": ".interactions",
    "Colour": ".colour",
    "ColourLike": ".colour",
    "CommandType": ".enums",
    "Commands": ".interactions",
    "Context": ".interactions",
    "Component": ".ui",
    "Components": ".interactions",
    "Container": ".ui",
    "CustomId": ".interactions",
    "Default": ".ui",
    "DiscordAPIError": ".http_service",
    "DiscordHTTPClient": ".http_service",
    "DiscordHTTPWorker": ".http_service",
    "DiscordServerError": ".http_service",
    "DiscordState": ".state",
    "DownloadError": ".files",
    "download": ".files",
    "Draft": ".ui",
    "Embed": ".ui",
    "EmbedAuthor": ".ui",
    "EmbedField": ".ui",
    "EmbedFooter": ".ui",
    "Emoji": ".ui",
    "File": ".ui",
    "FileUpload": ".ui",
    "Forbidden": ".http_service",
    "GroupOption": ".ui",
    "Guild": ".objects",
    "Interaction": ".interactions",
    "InteractionType": ".enums",
    "KnownGuild": ".state",
    "Label": ".ui",
    "MediaGallery": ".ui",
    "MediaItem": ".ui",
    "Member": ".objects",
    "MentionableSelect": ".ui",
    "Message": ".objects",
    "Modal": ".ui",
    "Modals": ".interactions",
    "NotFound": ".http_service",
    "Object": ".objects",
    "Option": ".interactions",
    "OverwriteType": ".enums",
    "PermissionOverwrite": ".objects",
    "Permissions": ".permissions",
    "RadioGroup": ".ui",
    "RateLimited": ".http_service",
    "Role": ".objects",
    "RoleSelect": ".ui",
    "Section": ".ui",
    "SelectOption": ".ui",
    "Separator": ".ui",
    "StringSelect": ".ui",
    "TextDisplay": ".ui",
    "TextInput": ".ui",
    "TextInputStyle": ".enums",
    "Thumbnail": ".ui",
    "Unauthorized": ".http_service",
    "Upload": ".ui",
    "User": ".objects",
    "UserSelect": ".ui",
    "Err": "micro.result",
    "Ok": "micro.result",
    "Result": "micro.result",
  },
)

__all__ = [
  "ActionRow",
  "AllowedMentions",
  "Asset",
  "Attachment",
  "BadRequest",
  "Button",
  "ButtonStyle",
  "Channel",
  "ChannelSelect",
  "ChannelType",
  "Checkbox",
  "CheckboxGroup",
  "Choice",
  "Colour",
  "ColourLike",
  "CommandType",
  "Commands",
  "Component",
  "Components",
  "Container",
  "Context",
  "CustomId",
  "Default",
  "DiscordAPIError",
  "DiscordHTTPClient",
  "DiscordHTTPWorker",
  "DiscordServerError",
  "DiscordState",
  "DownloadError",
  "Draft",
  "Embed",
  "EmbedAuthor",
  "EmbedField",
  "EmbedFooter",
  "Emoji",
  "Err",
  "File",
  "FileUpload",
  "Forbidden",
  "GroupOption",
  "Guild",
  "GuildEmoji",
  "Interaction",
  "InteractionType",
  "KnownGuild",
  "Label",
  "MediaGallery",
  "MediaItem",
  "Member",
  "MentionableSelect",
  "Message",
  "Modal",
  "Modals",
  "NotFound",
  "Object",
  "Ok",
  "Option",
  "OverwriteType",
  "PermissionOverwrite",
  "Permissions",
  "Presence",
  "RadioGroup",
  "RateLimited",
  "Result",
  "Role",
  "RoleSelect",
  "ScheduledEvent",
  "Section",
  "SelectOption",
  "Separator",
  "StageInstance",
  "Sticker",
  "StringSelect",
  "TextDisplay",
  "TextInput",
  "TextInputStyle",
  "Thumbnail",
  "Unauthorized",
  "Upload",
  "User",
  "UserSelect",
  "VoiceState",
  "asset",
  "colour",
  "download",
  "enums",
  "filters",
  "http_operations",
  "http_service",
  "interactions",
  "invite",
  "models",
  "objects",
  "permissions",
  "routes",
  "state",
  "text",
  "ui",
]
