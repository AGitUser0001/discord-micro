# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Union
from micro.discord._model import DiscordModel
from pydantic import AnyUrl, AwareDatetime, ConfigDict, Field, RootModel
from typing_extensions import TypeAliasType

from ._flags import Flags
from ._lobby_member_request import LobbyMemberRequest


class CreateLobbyRequest(DiscordModel):
    model_config = ConfigDict(
        extra='allow',
    )
    idle_timeout_seconds: Annotated[int | None, Field(ge=5, le=604800)] = None
    members: Annotated[list[LobbyMemberRequest] | None, Field(max_length=25)] = None
    metadata: dict[str, Any] | None = None
    flags: Flags | None = None
    override_event_webhooks_url: AnyUrl | None = None
    name: Annotated[str | None, Field(max_length=100, min_length=1)] = None
