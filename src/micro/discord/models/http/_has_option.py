# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class HasOption(StrEnum):
    LINK = 'link'
    EMBED = 'embed'
    FILE = 'file'
    IMAGE = 'image'
    VIDEO = 'video'
    SOUND = 'sound'
    STICKER = 'sticker'
    POLL = 'poll'
    SNAPSHOT = 'snapshot'
    NO_LINK = '-link'
    NO_EMBED = '-embed'
    NO_FILE = '-file'
    NO_IMAGE = '-image'
    NO_VIDEO = '-video'
    NO_SOUND = '-sound'
    NO_STICKER = '-sticker'
    NO_POLL = '-poll'
    NO_SNAPSHOT = '-snapshot'
