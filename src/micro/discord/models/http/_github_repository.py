# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType



class GithubRepository(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: int
    html_url: AnyUrl
    name: Annotated[str, Field(max_length=152133)]
    full_name: Annotated[str, Field(max_length=152133)]
