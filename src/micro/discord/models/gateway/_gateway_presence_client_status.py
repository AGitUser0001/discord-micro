# Generated from Discord's API specification. Do not edit directly.

from enum import IntEnum, IntFlag, StrEnum
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, RootModel

from ._desktop import Desktop
from ._mobile import Mobile
from ._web import Web
from ._vr import Vr


class GatewayPresenceClientStatus(BaseModel):
    model_config = ConfigDict(
        extra='allow',
    )
    desktop: Annotated[
        Desktop | None,
        Field(
            description="The user's status set for an active desktop (Windows, Linux, Mac) application session"
        ),
    ] = None
    mobile: Annotated[
        Mobile | None,
        Field(
            description="The user's status set for an active mobile (iOS, Android) application session"
        ),
    ] = None
    web: Annotated[
        Web | None,
        Field(
            description="The user's status set for an active web (browser, bot account) application session"
        ),
    ] = None
    vr: Annotated[
        Vr | None,
        Field(
            description="The user's status set for an active virtual reality application session"
        ),
    ] = None
