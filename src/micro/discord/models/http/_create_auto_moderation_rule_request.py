# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._keyword_upsert_request import KeywordUpsertRequest
from ._ml_spam_upsert_request import MLSpamUpsertRequest
from ._mention_spam_upsert_request import MentionSpamUpsertRequest
from ._user_profile_upsert_request import UserProfileUpsertRequest
from ._default_keyword_list_upsert_request import DefaultKeywordListUpsertRequest


class CreateAutoModerationRuleRequest(
    RootModel[
        DefaultKeywordListUpsertRequest
        | KeywordUpsertRequest
        | MLSpamUpsertRequest
        | MentionSpamUpsertRequest
        | UserProfileUpsertRequest
    ]
):
    root: (
        DefaultKeywordListUpsertRequest
        | KeywordUpsertRequest
        | MLSpamUpsertRequest
        | MentionSpamUpsertRequest
        | UserProfileUpsertRequest
    )
