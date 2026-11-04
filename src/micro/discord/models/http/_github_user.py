# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class GithubUser(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: int
    login: Annotated[str, Field(max_length=152133)]
    html_url: AnyUrl
    avatar_url: AnyUrl
