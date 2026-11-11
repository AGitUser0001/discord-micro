# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._error import Error


class RatelimitedResponse(Error):
    model_config = ConfigDict(
        extra='allow',
    )
    retry_after: Annotated[
        float,
        Field(description='The number of seconds to wait before retrying your request'),
    ]
    global_: Annotated[
        bool,
        Field(
            alias='global',
            description='Whether you are being ratelimited by the global ratelimit or a per-endpoint ratelimit',
        ),
    ]
