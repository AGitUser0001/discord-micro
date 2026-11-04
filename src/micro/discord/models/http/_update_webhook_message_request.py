# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._incoming_webhook_update_request_partial import IncomingWebhookUpdateRequestPartial


class UpdateWebhookMessageRequest(IncomingWebhookUpdateRequestPartial):
    model_config = ConfigDict(
        extra='allow',
    )
    files_0_: Annotated[bytes | None, Field(alias='files[0]')] = None
    files_1_: Annotated[bytes | None, Field(alias='files[1]')] = None
    files_2_: Annotated[bytes | None, Field(alias='files[2]')] = None
    files_3_: Annotated[bytes | None, Field(alias='files[3]')] = None
    files_4_: Annotated[bytes | None, Field(alias='files[4]')] = None
    files_5_: Annotated[bytes | None, Field(alias='files[5]')] = None
    files_6_: Annotated[bytes | None, Field(alias='files[6]')] = None
    files_7_: Annotated[bytes | None, Field(alias='files[7]')] = None
    files_8_: Annotated[bytes | None, Field(alias='files[8]')] = None
    files_9_: Annotated[bytes | None, Field(alias='files[9]')] = None
