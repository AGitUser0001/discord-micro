# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._create_text_thread_without_message_request import CreateTextThreadWithoutMessageRequest
from ._create_forum_thread_request import CreateForumThreadRequest


class CreateThreadRequest(
    RootModel[CreateForumThreadRequest | CreateTextThreadWithoutMessageRequest]
):
    root: CreateForumThreadRequest | CreateTextThreadWithoutMessageRequest
