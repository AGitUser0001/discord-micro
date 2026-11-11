# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._keyword_upsert_request_partial import KeywordUpsertRequestPartial
from ._ml_spam_upsert_request_partial import MLSpamUpsertRequestPartial
from ._mention_spam_upsert_request_partial import MentionSpamUpsertRequestPartial
from ._user_profile_upsert_request_partial import UserProfileUpsertRequestPartial
from ._default_keyword_list_upsert_request_partial import DefaultKeywordListUpsertRequestPartial


class UpdateAutoModerationRuleRequest(
    RootModel[
        DefaultKeywordListUpsertRequestPartial
        | KeywordUpsertRequestPartial
        | MLSpamUpsertRequestPartial
        | MentionSpamUpsertRequestPartial
        | UserProfileUpsertRequestPartial
    ]
):
    root: (
        DefaultKeywordListUpsertRequestPartial
        | KeywordUpsertRequestPartial
        | MLSpamUpsertRequestPartial
        | MentionSpamUpsertRequestPartial
        | UserProfileUpsertRequestPartial
    )
