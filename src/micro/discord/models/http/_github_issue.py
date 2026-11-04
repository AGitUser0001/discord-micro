# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._github_user import GithubUser


class GithubIssue(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    id: int
    number: int
    html_url: AnyUrl
    user: GithubUser
    title: Annotated[str, Field(max_length=152133)]
    body: Annotated[str | None, Field(max_length=152133)] = None
    pull_request: Any | None = None
