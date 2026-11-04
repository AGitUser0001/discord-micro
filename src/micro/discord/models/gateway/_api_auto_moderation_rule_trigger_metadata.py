# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._preset import Preset


class APIAutoModerationRuleTriggerMetadata(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    keyword_filter: Annotated[
        list[str] | None,
        Field(
            description='Substrings which will be searched for in content (Maximum of 1000)\n\nA keyword can be a phrase which contains multiple words. Wildcard symbols can be used to customize how each string will be matched. Each keyword must be 60 characters or less'
        ),
    ] = None
    presets: Annotated[
        list[Preset] | None,
        Field(
            description='The internally pre-defined wordsets which will be searched for in content\n\nAssociated trigger type: AutoModerationRuleTriggerType.KeywordPreset'
        ),
    ] = None
    allow_list: Annotated[
        list[str] | None,
        Field(
            description='Substrings which will be exempt from triggering the preset trigger type (Maximum of 1000)\n\nA allowed-word can be a phrase which contains multiple words. Wildcard symbols can be used to customize how each string will be matched. Each keyword must be 60 characters or less'
        ),
    ] = None
    regex_patterns: Annotated[
        list[str] | None,
        Field(
            description='Regular expression patterns which will be matched against content (Maximum of 10)\n\nOnly Rust flavored regex is currently supported (Maximum of 260 characters)\n\nAssociated trigger types: AutoModerationRuleTriggerType.Keyword, AutoModerationRuleTriggerType.MemberProfile'
        ),
    ] = None
    mention_total_limit: Annotated[
        float | None,
        Field(
            description='Total number of mentions (role & user) allowed per message (Maximum of 50)\n\nAssociated trigger type: AutoModerationRuleTriggerType.MentionSpam'
        ),
    ] = None
    mention_raid_protection_enabled: Annotated[
        bool | None,
        Field(
            description='Whether to automatically detect mention raids\n\nAssociated trigger type: AutoModerationRuleTriggerType.MentionSpam'
        ),
    ] = None
