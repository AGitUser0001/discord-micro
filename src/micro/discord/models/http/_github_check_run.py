# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._github_check_pull_request import GithubCheckPullRequest
from ._github_check_run_output import GithubCheckRunOutput
from ._github_check_suite import GithubCheckSuite


class GithubCheckRun(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    conclusion: Annotated[str | None, Field(max_length=152133)] = None
    name: Annotated[str, Field(max_length=152133)]
    html_url: AnyUrl
    check_suite: GithubCheckSuite
    details_url: AnyUrl | None = None
    output: GithubCheckRunOutput | None = None
    pull_requests: Annotated[
        list[GithubCheckPullRequest] | None, Field(max_length=1521)
    ] = None
