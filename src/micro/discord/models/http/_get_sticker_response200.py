# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._standard_sticker_response import StandardStickerResponse
from ._guild_sticker_response import GuildStickerResponse


class GetStickerResponse200(RootModel[GuildStickerResponse | StandardStickerResponse]):
    root: GuildStickerResponse | StandardStickerResponse
