# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._github_check_app import GithubCheckApp
from ._github_check_pull_request import GithubCheckPullRequest


class GithubCheckSuite(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    conclusion: Annotated[str | None, Field(max_length=152133)] = None
    head_branch: Annotated[str | None, Field(max_length=152133)] = None
    head_sha: Annotated[str, Field(max_length=152133)]
    pull_requests: Annotated[
        list[GithubCheckPullRequest] | None, Field(max_length=1521)
    ] = None
    app: GithubCheckApp
