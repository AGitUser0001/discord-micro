# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._keyword_rule_response import KeywordRuleResponse
from ._ml_spam_rule_response import MLSpamRuleResponse
from ._mention_spam_rule_response import MentionSpamRuleResponse
from ._user_profile_rule_response import UserProfileRuleResponse
from ._default_keyword_rule_response import DefaultKeywordRuleResponse


class GetAutoModerationRuleResponse200(
    RootModel[
        DefaultKeywordRuleResponse
        | KeywordRuleResponse
        | MLSpamRuleResponse
        | MentionSpamRuleResponse
        | UserProfileRuleResponse
    ]
):
    root: (
        DefaultKeywordRuleResponse
        | KeywordRuleResponse
        | MLSpamRuleResponse
        | MentionSpamRuleResponse
        | UserProfileRuleResponse
    )
