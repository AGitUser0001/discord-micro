# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._github_check_suite import GithubCheckSuite
from ._github_commit import GithubCommit
from ._github_repository import GithubRepository
from ._github_user import GithubUser
from ._github_check_run import GithubCheckRun
from ._github_comment import GithubComment
from ._github_discussion import GithubDiscussion
from ._github_issue import GithubIssue
from ._github_release import GithubRelease
from ._github_review import GithubReview


class GithubWebhook(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    action: Annotated[str | None, Field(max_length=152133)] = None
    ref: Annotated[str | None, Field(max_length=152133)] = None
    ref_type: Annotated[str | None, Field(max_length=152133)] = None
    comment: GithubComment | None = None
    issue: GithubIssue | None = None
    pull_request: GithubIssue | None = None
    repository: GithubRepository | None = None
    forkee: GithubRepository | None = None
    sender: GithubUser
    member: GithubUser | None = None
    release: GithubRelease | None = None
    head_commit: GithubCommit | None = None
    commits: Annotated[list[GithubCommit] | None, Field(max_length=1521)] = None
    forced: bool | None = None
    compare: AnyUrl | None = None
    review: GithubReview | None = None
    check_run: GithubCheckRun | None = None
    check_suite: GithubCheckSuite | None = None
    discussion: GithubDiscussion | None = None
    answer: GithubComment | None = None
