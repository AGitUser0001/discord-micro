# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel



class Type9(StrEnum):
    article = 'article'
    auto_moderation_message = 'auto_moderation_message'
    gifv = 'gifv'
    image = 'image'
    link = 'link'
    poll_result = 'poll_result'
    rich = 'rich'
    video = 'video'
