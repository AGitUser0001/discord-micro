# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class SearchableEmbedType(StrEnum):
    IMAGE = 'image'
    VIDEO = 'video'
    GIFV = 'gif'
    SOUND = 'sound'
    ARTICLE = 'article'
